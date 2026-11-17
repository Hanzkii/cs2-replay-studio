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
            if self.connected and self.sock:
                return True
            now = time.time()
            if now - self.last_attempt_time < 1.5:
                return self.connected
            self.last_attempt_time = now

            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.6)
                s.connect((self.host, self.port))
                s.setblocking(False)
                self.sock = s
                self.connected = True
                return True
            except Exception:
                self.connected = False
                self.sock = None
                return False

    def is_connected(self) -> bool:
        return self.connected and self.sock is not None

    def send_command(self, cmd: str) -> bool:
        """Sends raw console command string to CS2 via Netcon."""
        if not self.is_connected():
            if not self.try_connect():
                return False
        with self._lock:
            if not self.sock:
                return False
            try:
                payload = (cmd.strip() + "\n").encode("utf-8")
                self.sock.sendall(payload)
                return True
            except Exception:
                self.connected = False
                self.sock = None
                return False

    def goto_tick(self, tick: int) -> bool:
        """Seeks CS2 demo playback to specified tick."""
        return self.send_command(f"demo_gototick {max(0, int(tick))}")

    def toggle_pause(self) -> bool:
        """Toggles play/pause state in CS2 demo playback."""
        return self.send_command("demo_togglepause")

    def pause(self) -> bool:
        """Pauses CS2 demo playback."""
        return self.send_command("demo_pause")

    def resume(self) -> bool:
        """Resumes CS2 demo playback."""
        return self.send_command("demo_resume")

    def set_timescale(self, scale: float) -> bool:
        """Sets playback speed multiplier (e.g. 0.25, 0.5, 1.0, 2.0)."""
        return self.send_command(f"demo_timescale {scale:.2f}")

    def spec_player(self, player_name: str) -> bool:
        """Locks spectator camera onto the specified player name."""
        clean_name = player_name.strip().strip('"')
        return self.send_command(f'spec_player "{clean_name}"')

    def spec_mode(self, mode: int) -> bool:
        """Sets spectator camera perspective: 1=First Person, 2=Chase/3rd Person, 6=Free Roam."""
        return self.send_command(f"spec_mode {mode}")

    def jump_and_inspect(self, tick: int, player_name: str, lead_ticks: int = 96, timescale: float = 0.25) -> bool:
        """
        Executes a reinforced jump-to-action audit sequence:
        1. Jumps to (tick - lead_ticks) so the buildup/movement is clearly visible.
        2. Sets slow-motion playback speed.
        3. Forces First-Person camera (spec_mode 1).
        4. Locks spectator target to player_name.
        5. Reinforces in background after 250ms to ensure the engine doesn't revert to director camera.
        """
        lead_tick = max(0, int(tick) - int(lead_ticks))
        clean_name = player_name.strip().strip('"')

        # Batch initial burst
        commands = [
            f"demo_gototick {lead_tick}",
            f"demo_timescale {timescale:.2f}",
            "spec_mode 1",
            f'spec_player "{clean_name}"'
        ]
        batch_payload = "\n".join(commands)
        res = self.send_command(batch_payload)

        # Background thread reinforcement once tick seek completes
        def _reinforce():
            time.sleep(0.25)
            self.send_command(f'spec_player "{clean_name}"\nspec_mode 1\ndemo_timescale {timescale:.2f}')

        threading.Thread(target=_reinforce, daemon=True).start()
        return res

    def toggle_lag_compensation_box(self) -> bool:
        """Toggles in-engine lag compensation debug hitboxes."""
        return self.send_command("toggle sv_showlagcompensation 0 1")

    def toggle_bullet_impacts(self) -> bool:
        """Toggles client/server bullet impact visualization."""
        return self.send_command("toggle sv_showimpacts 0 1")

    def toggle_wireframe_models(self) -> bool:
        """Toggles wireframe player model rendering."""
        return self.send_command("toggle r_drawothermodels 1 2")

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
