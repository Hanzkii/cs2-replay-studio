#!/usr/bin/env python3
"""
engine_link.py - Steam/CS2 Auto-Discovery & Netcon Loopback Console Client

Handles:
  1. Dynamic Windows Registry scanning to locate Steam installation and libraryfolders.vdf.
  2. Automatic discovery of Counter-Strike 2 executable (cs2.exe) and csgo/ game directory.
  3. Non-blocking TCP socket link to CS2 console (-netconport) for real-time demo controls.
"""

import os
import sys
import re
import socket
import threading
import time
from typing import Optional, List, Tuple


class CS2Locator:
    """Discovers Steam and CS2 installations dynamically on Windows."""

    @staticmethod
    def find_steam_root() -> Optional[str]:
        if sys.platform != "win32":
            return None
        try:
            import winreg
            for root_key in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
                for sub_key in (r"Software\Valve\Steam", r"SOFTWARE\WOW6432Node\Valve\Steam"):
                    try:
                        with winreg.OpenKey(root_key, sub_key) as key:
                            val, _ = winreg.QueryValueEx(key, "SteamPath")
                            if val and os.path.exists(val):
                                return os.path.normpath(val)
                    except OSError:
                        continue
        except Exception:
            pass
        return None

    @staticmethod
    def get_all_steam_libraries(steam_root: str) -> List[str]:
        libraries = [steam_root]
        vdf_path = os.path.join(steam_root, "steamapps", "libraryfolders.vdf")
        if not os.path.exists(vdf_path):
            return libraries

        try:
            with open(vdf_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            for match in re.finditer(r'"path"\s+"([^"]+)"', content):
                raw_path = match.group(1).replace("\\\\", "\\")
                norm_path = os.path.normpath(raw_path)
                if os.path.exists(norm_path) and norm_path not in libraries:
                    libraries.append(norm_path)
        except Exception:
            pass
        return libraries

    @classmethod
    def find_cs2(cls) -> Optional[Tuple[str, str]]:
        """
        Returns (cs2_exe_path, cs2_game_dir) or None.
        Dynamically searches all Steam libraries.
        """
        steam_root = cls.find_steam_root()
        if not steam_root:
            return None

        libs = cls.get_all_steam_libraries(steam_root)
        for lib in libs:
            cs2_bin = os.path.join(lib, "steamapps", "common", "Counter-Strike Global Offensive", "game", "bin", "win64", "cs2.exe")
            if os.path.exists(cs2_bin):
                csgo_dir = os.path.join(lib, "steamapps", "common", "Counter-Strike Global Offensive", "game", "csgo")
                return os.path.normpath(cs2_bin), os.path.normpath(csgo_dir)

        return None


class CS2NetconClient:
    """Non-blocking TCP socket client for CS2 console communication."""

    def __init__(self, port: int = 2121, host: str = "127.0.0.1"):
        self.host = host
        self.port = port
        self.sock: Optional[socket.socket] = None
        self.connected = False
        self._lock = threading.Lock()
        self.last_attempt_time = 0.0

    def try_connect(self) -> bool:
        with self._lock:
            if self.connected:
                return True
            now = time.time()
            if now - self.last_attempt_time < 2.0:
                return False
            self.last_attempt_time = now

            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.5)
                s.connect((self.host, self.port))
                s.setblocking(False)
                self.sock = s
                self.connected = True
                return True
            except Exception:
                self.connected = False
                self.sock = None
                return False

    def send_command(self, cmd: str) -> bool:
        with self._lock:
            if not self.connected or not self.sock:
                return False
            try:
                payload = (cmd.strip() + "\n").encode("utf-8")
                self.sock.sendall(payload)
                return True
            except Exception:
                self.connected = False
                self.sock = None
                return False

    def read_output(self) -> str:
        with self._lock:
            if not self.connected or not self.sock:
                return ""
            chunks = []
            while True:
                try:
                    data = self.sock.recv(4096)
                    if not data:
                        self.connected = False
                        self.sock = None
                        break
                    chunks.append(data)
                    if len(data) < 4096:
                        break
                except (BlockingIOError, socket.timeout):
                    break
                except Exception:
                    self.connected = False
                    self.sock = None
                    break
            return b"".join(chunks).decode("utf-8", "ignore") if chunks else ""

    def disconnect(self):
        with self._lock:
            if self.sock:
                try:
                    self.sock.close()
                except Exception:
                    pass
            self.sock = None
            self.connected = False
