#!/usr/bin/env python3
"""
launcher.py - Counter-Strike 2 Sub-Tick Replay Studio Desktop GUI Control Center

An intuitive, dark-themed native desktop control center for Counter-Strike 2 players,
analysts, and coaches to inspect match replays (.dem) with in-game sub-tick overlays:
  1. Automated dynamic detection of Steam and cs2.exe across all library drives.
  2. Drag-and-drop or file browsing for CS2 match recordings (.dem) with instant metadata parsing.
  3. Interactive layer toggles (Sub-Tick bar, 3D rewound hitbox, ray-traces, anomalies).
  4. 1-Click Launch: automatically stages demo, starts CS2 in borderless windowed mode,
     and snaps the transparent HUD overlay seamlessly.
  5. Built-in live telemetry and anomaly diagnostics console.

Zero pip dependencies: Pure Python standard library (tkinter + ctypes + socket).
"""

import os
import sys
import shutil
import subprocess
import threading
import time
import io
import json
import zipfile
import urllib.request
from typing import Optional, Dict, Any

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from engine_link import CS2Locator, CS2NetconClient
from demo_parser import CS2DemoSummary


class ReplayStudioLauncherApp:
    """Desktop GUI Control Center for CS2 Replay Overlay."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("CS2 Sub-Tick Replay Studio // Desktop Control Center")
        self.root.geometry("960x760")
        self.root.minsize(860, 680)

        # Apply dark theme styling
        self.bg_dark = "#090d16"
        self.card_bg = "#111827"
        self.border_col = "#1f2937"
        self.accent_cyan = "#38bdf8"
        self.accent_indigo = "#818cf8"
        self.accent_emerald = "#34d399"
        self.accent_coral = "#f43f5e"
        self.text_main = "#f8fafc"
        self.text_muted = "#94a3b8"

        self.root.config(bg=self.bg_dark)

        # State Variables
        self.app_dir = os.path.dirname(os.path.abspath(__file__))
        self.local_version = self._load_local_version()
        self.selected_demo_path: Optional[str] = None
        self.demo_info: Dict[str, Any] = {}
        self.cs2_exe: Optional[str] = None
        self.cs2_dir: Optional[str] = None

        self.cs2_proc: Optional[subprocess.Popen] = None
        self.overlay_proc: Optional[subprocess.Popen] = None

        # Checkbox states
        self.var_subtick = tk.BooleanVar(value=True)
        self.var_hitbox = tk.BooleanVar(value=True)
        self.var_raytrace = tk.BooleanVar(value=True)
        self.var_anomalies = tk.BooleanVar(value=True)
        self.var_crosshair = tk.BooleanVar(value=True)
        self.var_borderless = tk.BooleanVar(value=True)
        self.var_launch_external_overlay = tk.BooleanVar(value=False)
        self.var_netcon_port = tk.StringVar(value="2121")

        # Discover CS2 initially
        self._discover_cs2()

        # Build UI layout
        self._build_ui()

        # Check if demo path passed via command line
        if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
            self.load_demo(sys.argv[1])

        # Initial log notice
        self.log("CS2 Sub-Tick Replay Studio Desktop Launcher initialized.")
        if self.cs2_exe:
            self.log(f"Auto-detected Counter-Strike 2: {os.path.basename(self.cs2_exe)}")
        else:
            self.log("Note: CS2 executable not found in default Steam libraries. Please click 'Browse cs2.exe'.")

    def _discover_cs2(self):
        info = CS2Locator.find_cs2()
        if info:
            self.cs2_exe, self.cs2_dir = info

    def _build_ui(self):
        # 1. Top Header Bar
        header = tk.Frame(self.root, bg="#0d1117", height=64, padx=20, pady=12)
        header.pack(fill="x", side="top")

        title_lbl = tk.Label(
            header,
            text="COUNTER-STRIKE 2 // SUB-TICK REPLAY STUDIO",
            font=("Segoe UI", 13, "bold"),
            fg=self.accent_cyan,
            bg="#0d1117"
        )
        title_lbl.pack(side="left")

        badge_lbl = tk.Label(
            header,
            text="PBDEMS2 WIRE ENGINE",
            font=("Consolas", 9, "bold"),
            fg="#c084fc",
            bg="#2e1065",
            padx=8, pady=2
        )
        badge_lbl.pack(side="left", padx=(12, 6))

        ver_lbl = tk.Label(
            header,
            text=f"build {self.local_version.get('commit_sha', '0cd56d7')[:7]}",
            font=("Consolas", 8),
            fg="#64748b",
            bg="#0d1117"
        )
        ver_lbl.pack(side="left")

        status_txt = "CS2 Ready" if self.cs2_exe else "CS2 Not Found"
        status_col = self.accent_emerald if self.cs2_exe else self.accent_coral
        self.lbl_engine_status = tk.Label(
            header,
            text=f"● {status_txt}",
            font=("Consolas", 10, "bold"),
            fg=status_col,
            bg="#0d1117"
        )
        self.lbl_engine_status.pack(side="right", padx=(8, 0))

        # Header utility buttons: Update & Desktop Shortcut
        self.btn_update = tk.Button(
            header,
            text="🔄 Update Tool",
            font=("Segoe UI", 9, "bold"),
            bg="#1e293b",
            fg=self.accent_cyan,
            activebackground="#334155",
            activeforeground="#ffffff",
            relief="flat",
            padx=10,
            pady=3,
            cursor="hand2",
            command=self.check_and_install_updates
        )
        self.btn_update.pack(side="right", padx=6)

        self.btn_shortcut = tk.Button(
            header,
            text="📌 Desktop Icon",
            font=("Segoe UI", 9, "bold"),
            bg="#1e293b",
            fg=self.accent_emerald,
            activebackground="#334155",
            activeforeground="#ffffff",
            relief="flat",
            padx=10,
            pady=3,
            cursor="hand2",
            command=self.create_desktop_shortcut
        )
        self.btn_shortcut.pack(side="right", padx=6)

        # 2. Main Scrollable Container
        main_frame = tk.Frame(self.root, bg=self.bg_dark, padx=16, pady=12)
        main_frame.pack(fill="both", expand=True)

        # Split into Left and Right Columns
        col_left = tk.Frame(main_frame, bg=self.bg_dark)
        col_left.pack(side="left", fill="both", expand=True, padx=(0, 8))

        col_right = tk.Frame(main_frame, bg=self.bg_dark)
        col_right.pack(side="right", fill="both", expand=True, padx=(8, 0))

        # --- LEFT COLUMN: Match Recording & CS2 Engine ---
        self._build_demo_card(col_left)
        self._build_cs2_card(col_left)

        # --- RIGHT COLUMN: Overlay Config & Hotkeys ---
        self._build_overlay_card(col_right)
        self._build_hotkey_card(col_right)

        # 3. Bottom Execution Bar
        action_bar = tk.Frame(self.root, bg="#0f172a", padx=20, pady=14, relief="ridge", bd=1)
        action_bar.pack(fill="x", side="bottom")

        self.btn_launch_all = tk.Button(
            action_bar,
            text="▶  LAUNCH REPLAY (NATIVE PANORAMA HUD)",
            font=("Segoe UI", 11, "bold"),
            bg="#059669",
            fg="#ffffff",
            activebackground="#10b981",
            activeforeground="#ffffff",
            relief="flat",
            padx=20, pady=8,
            cursor="hand2",
            command=self.launch_full_replay
        )
        self.btn_launch_all.pack(side="left")

        self.chk_ext_overlay = tk.Checkbutton(
            action_bar,
            text="Also run external Python overlay",
            variable=self.var_launch_external_overlay,
            font=("Segoe UI", 9),
            bg=self.bg_dark,
            fg=self.text_muted,
            selectcolor="#0f172a",
            activebackground=self.bg_dark,
            activeforeground="#ffffff"
        )
        self.chk_ext_overlay.pack(side="left", padx=12)

        self.btn_launch_overlay_only = tk.Button(
            action_bar,
            text="⚙ Overlay Only",
            font=("Segoe UI", 9, "bold"),
            bg="#1e293b",
            fg="#e2e8f0",
            relief="flat",
            padx=14, pady=8,
            cursor="hand2",
            command=self.launch_overlay_only
        )
        self.btn_launch_overlay_only.pack(side="left", padx=(0, 10))

        self.btn_stop = tk.Button(
            action_bar,
            text="⏹ Stop Session",
            font=("Segoe UI", 9, "bold"),
            bg="#450a0a",
            fg="#fca5a5",
            relief="flat",
            padx=14, pady=8,
            cursor="hand2",
            command=self.stop_all
        )
        self.btn_stop.pack(side="left")

        # 4. Embedded Live Diagnostics Console
        console_frame = tk.Frame(self.root, bg="#030712", padx=12, pady=6)
        console_frame.pack(fill="x", side="bottom")

        console_title = tk.Label(
            console_frame,
            text="LIVE DIAGNOSTICS & TELEMETRY LOG",
            font=("Consolas", 8, "bold"),
            fg="#64748b",
            bg="#030712"
        )
        console_title.pack(anchor="w")

        self.txt_console = tk.Text(
            console_frame,
            height=6,
            bg="#030712",
            fg=self.accent_cyan,
            font=("Consolas", 9),
            insertbackground="#ffffff",
            relief="flat",
            wrap="word"
        )
        self.txt_console.pack(fill="x", expand=True)

    def _build_demo_card(self, parent):
        card = tk.LabelFrame(
            parent,
            text=" 1. MATCH RECORDING (.DEM) INGESTION ",
            font=("Consolas", 9, "bold"),
            bg=self.card_bg,
            fg=self.accent_indigo,
            padx=14, pady=12,
            relief="groove", bd=1
        )
        card.pack(fill="x", pady=(0, 12))

        btn_row = tk.Frame(card, bg=self.card_bg)
        btn_row.pack(fill="x", pady=(0, 8))

        btn_browse = tk.Button(
            btn_row,
            text="📁 Browse .dem File...",
            font=("Segoe UI", 9, "bold"),
            bg="#3b82f6", fg="#ffffff",
            relief="flat", padx=12, pady=4,
            cursor="hand2",
            command=self.browse_demo_file
        )
        btn_browse.pack(side="left")

        self.lbl_demo_file = tk.Label(
            card,
            text="No demo file loaded. (Browse or drag & drop a .dem file)",
            font=("Consolas", 9),
            fg=self.text_muted,
            bg=self.card_bg,
            anchor="w"
        )
        self.lbl_demo_file.pack(fill="x", pady=(0, 6))

        # Metadata grid
        self.grid_meta = tk.Frame(card, bg="#0f172a", padx=10, pady=8, relief="ridge", bd=1)
        self.grid_meta.pack(fill="x")

        self.lbl_meta_map = tk.Label(self.grid_meta, text="Map: --", font=("Consolas", 9), fg=self.text_muted, bg="#0f172a")
        self.lbl_meta_map.grid(row=0, column=0, sticky="w", padx=6, pady=2)

        self.lbl_meta_tick = tk.Label(self.grid_meta, text="Tickrate: --", font=("Consolas", 9), fg=self.text_muted, bg="#0f172a")
        self.lbl_meta_tick.grid(row=0, column=1, sticky="w", padx=6, pady=2)

        self.lbl_meta_build = tk.Label(self.grid_meta, text="Build: --", font=("Consolas", 9), fg=self.text_muted, bg="#0f172a")
        self.lbl_meta_build.grid(row=1, column=0, sticky="w", padx=6, pady=2)

        self.lbl_meta_dur = tk.Label(self.grid_meta, text="Duration: --", font=("Consolas", 9), fg=self.text_muted, bg="#0f172a")
        self.lbl_meta_dur.grid(row=1, column=1, sticky="w", padx=6, pady=2)

    def _build_cs2_card(self, parent):
        card = tk.LabelFrame(
            parent,
            text=" 2. COUNTER-STRIKE 2 ENGINE LINK ",
            font=("Consolas", 9, "bold"),
            bg=self.card_bg,
            fg=self.accent_indigo,
            padx=14, pady=12,
            relief="groove", bd=1
        )
        card.pack(fill="x")

        exe_text = os.path.basename(self.cs2_exe) if self.cs2_exe else "Not located automatically"
        self.lbl_cs2_path = tk.Label(
            card,
            text=f"Target: {exe_text}",
            font=("Consolas", 9),
            fg=self.accent_emerald if self.cs2_exe else self.accent_coral,
            bg=self.card_bg,
            anchor="w"
        )
        self.lbl_cs2_path.pack(fill="x", pady=(0, 6))

        btn_browse_cs2 = tk.Button(
            card,
            text="Change / Locate cs2.exe...",
            font=("Segoe UI", 8),
            bg="#1e293b", fg="#cbd5e1",
            relief="flat", padx=8, pady=2,
            cursor="hand2",
            command=self.browse_cs2_exe
        )
        btn_browse_cs2.pack(anchor="w", pady=(0, 8))

        # Launch parameters checklist
        chk_borderless = tk.Checkbutton(
            card,
            text="Launch in Borderless Windowed Mode (-windowed -noborder)",
            variable=self.var_borderless,
            font=("Segoe UI", 9),
            bg=self.card_bg, fg=self.text_main,
            selectcolor="#0f172a", activebackground=self.card_bg, activeforeground=self.text_main
        )
        chk_borderless.pack(anchor="w")

        port_row = tk.Frame(card, bg=self.card_bg)
        port_row.pack(fill="x", pady=(4, 0))
        tk.Label(port_row, text="Netcon Loopback Port:", font=("Segoe UI", 9), fg=self.text_muted, bg=self.card_bg).pack(side="left")
        port_entry = tk.Entry(port_row, textvariable=self.var_netcon_port, width=6, bg="#0f172a", fg=self.accent_cyan, insertbackground="#ffffff", font=("Consolas", 9))
        port_entry.pack(side="left", padx=6)

        btn_deploy_panorama = tk.Button(
            card,
            text="🎨 Deploy Native Panorama In-Game HUD...",
            font=("Segoe UI", 9, "bold"),
            bg="#1e1b4b", fg="#c084fc",
            activebackground="#2e1065", activeforeground="#ffffff",
            relief="flat", padx=10, pady=3,
            cursor="hand2",
            command=self.deploy_panorama_hud
        )
        btn_deploy_panorama.pack(anchor="w", pady=(8, 0))

    def _build_overlay_card(self, parent):
        card = tk.LabelFrame(
            parent,
            text=" 3. IN-GAME VISUAL OVERLAY LAYERS ",
            font=("Consolas", 9, "bold"),
            bg=self.card_bg,
            fg=self.accent_cyan,
            padx=14, pady=12,
            relief="groove", bd=1
        )
        card.pack(fill="x", pady=(0, 12))

        options = [
            ("Layer 1: Sub-Tick Micro-Slice Bar (15.625 ms discrete window)", self.var_subtick),
            ("Layer 2: 3D Rewound Lag Comp Hitbox (Apex Joint #6)", self.var_hitbox),
            ("Layer 3: Bullet Ray-Trace & Trajectory Vector", self.var_raytrace),
            ("Layer 4: Desync & Rollback Anomaly Alerts", self.var_anomalies),
            ("First-Person Crosshair Guide Reticle", self.var_crosshair),
        ]

        for text, var in options:
            chk = tk.Checkbutton(
                card,
                text=text,
                variable=var,
                font=("Segoe UI", 9),
                bg=self.card_bg, fg=self.text_main,
                selectcolor="#0f172a", activebackground=self.card_bg, activeforeground=self.text_main
            )
            chk.pack(anchor="w", pady=2)

    def _build_hotkey_card(self, parent):
        card = tk.LabelFrame(
            parent,
            text=" 4. IN-GAME HOTKEY CONTROLS ",
            font=("Consolas", 9, "bold"),
            bg=self.card_bg,
            fg=self.accent_cyan,
            padx=14, pady=10,
            relief="groove", bd=1
        )
        card.pack(fill="x")

        hotkeys = [
            ("[F1] / [INSERT]", "Toggle Settings & Anomaly Navigator (Unlocks mouse)"),
            ("[SPACE]", "Play / Pause CS2 demo playback"),
            ("[←] / [→]", "Seek ±64 Ticks (±1.0 second scrub)"),
            ("[F6]", "Trigger Test Shot & Sub-Tick Audit"),
            ("[F7]", "Toggle Live Always-On HUD vs Event-Only"),
            ("[F8]", "Cycle Cam Perspective (1st Person / Chase / Freecam)"),
            ("[F2] - [F5]", "Quick toggle Hitbox / Sub-Tick / Rays / Alerts"),
            ("[F11] / [F10]", "Emergency Master Hide / Reveal Overlay"),
        ]

        for key, desc in hotkeys:
            row = tk.Frame(card, bg=self.card_bg)
            row.pack(fill="x", pady=1.5)
            tk.Label(row, text=key, font=("Consolas", 9, "bold"), fg=self.accent_cyan, bg=self.card_bg, width=14, anchor="w").pack(side="left")
            tk.Label(row, text=desc, font=("Segoe UI", 9), fg=self.text_muted, bg=self.card_bg).pack(side="left")

    def browse_demo_file(self):
        f = filedialog.askopenfilename(
            title="Select Counter-Strike 2 Demo (.dem)",
            filetypes=[("CS2 Replay Demos", "*.dem;*.DEM"), ("All Files", "*.*")]
        )
        if f:
            self.load_demo(f)

    def load_demo(self, path: str):
        self.selected_demo_path = os.path.normpath(path)
        self.lbl_demo_file.config(text=f"Loaded: {os.path.basename(self.selected_demo_path)}", fg=self.text_main)
        self.log(f"Reading demo header: {os.path.basename(self.selected_demo_path)}")

        info = CS2DemoSummary.inspect_file(self.selected_demo_path)
        self.demo_info = info

        if info.get("valid"):
            self.lbl_meta_map.config(text=f"Map: {info.get('map_name', 'Unknown')}", fg=self.accent_cyan)
            self.lbl_meta_tick.config(text=f"Tickrate: {info.get('server_tickrate', 64.0)} Hz", fg=self.accent_emerald)
            self.lbl_meta_build.config(text=f"Build: {info.get('build_num', 'Unknown')}", fg=self.text_main)
            self.lbl_meta_dur.config(text=f"Size: {info.get('file_size_mb', 0)} MB ({info.get('duration_str', '')})", fg=self.text_main)
            self.log(f"Demo parsed: Map={info.get('map_name')}, Protocol={info.get('magic')}, Build={info.get('build_num')}")

            # Autoscan anomalies
            try:
                anoms = CS2DemoSummary.scan_anomalies(self.selected_demo_path, max_events=50)
                if anoms:
                    self.log(f"Autoscan detected {len(anoms)} combat actions & sub-tick anomalies! (Press [F1] in-game to jump).")
            except Exception:
                pass
        else:
            self.log(f"Warning parsing demo: {info.get('error', 'Unknown format')}")

    def deploy_panorama_hud(self, silent: bool = False):
        """Deploys native Panorama XML/CSS/JS files directly into game/csgo/panorama/."""
        if not self.cs2_dir or not os.path.exists(self.cs2_dir):
            if not silent:
                messagebox.showerror("CS2 Not Found", "Cannot deploy Panorama HUD: CS2 game directory not located.")
            return

        src_dir = os.path.join(self.app_dir, "panorama")
        target_dir = os.path.join(self.cs2_dir, "panorama")

        if not os.path.exists(src_dir):
            if not silent:
                messagebox.showerror("Error", f"Panorama source files not found at: {src_dir}")
            return

        try:
            shutil.copytree(src_dir, target_dir, dirs_exist_ok=True)
            self.log(f"Native Panorama HUD & Menu deployed to: {target_dir}")
            if not silent:
                messagebox.showinfo(
                    "Panorama HUD Deployed",
                    f"Successfully deployed native Panorama in-engine HUD & Menu to:\n\n{target_dir}\n\n"
                    f"When CS2 launches with -insecure, the native in-engine Panorama HUD and settings will load directly with authentic 1:1 CS2 visuals!"
                )
        except Exception as e:
            self.log(f"Failed to deploy Panorama HUD: {e}")
            if not silent:
                messagebox.showerror("Deploy Error", f"Failed to copy Panorama assets:\n{e}")

    def browse_cs2_exe(self):
        f = filedialog.askopenfilename(
            title="Locate cs2.exe",
            filetypes=[("CS2 Executable", "cs2.exe"), ("All Files", "*.*")]
        )
        if f and os.path.exists(f):
            self.cs2_exe = os.path.normpath(f)
            self.cs2_dir = os.path.normpath(os.path.join(os.path.dirname(f), "..", "..", "csgo"))
            self.lbl_cs2_path.config(text=f"Target: {os.path.basename(self.cs2_exe)}", fg=self.accent_emerald)
            self.lbl_engine_status.config(text="● CS2 Ready", fg=self.accent_emerald)
            self.log(f"Updated CS2 path: {os.path.basename(self.cs2_exe)}")

    def launch_full_replay(self):
        if not self.selected_demo_path or not os.path.exists(self.selected_demo_path):
            messagebox.showwarning("No Demo Selected", "Please select a .dem match recording first.")
            return

        if not self.cs2_exe or not os.path.exists(self.cs2_exe):
            messagebox.showerror("CS2 Not Found", "Counter-Strike 2 executable was not found. Please click 'Locate cs2.exe'.")
            return

        threading.Thread(target=self._launch_worker, daemon=True).start()

    def _monitor_cs2_process(self):
        """Watches CS2 process lifecycle and terminates companion overlay immediately upon game exit."""
        if self.cs2_proc:
            try:
                self.cs2_proc.wait()
                self.log("Counter-Strike 2 closed. Terminating companion overlay...")
                self.stop_all()
            except Exception:
                pass

    def _launch_worker(self):
        self.log("Preparing replay playback session...")

        # 1. Stage demo to CS2 game directory
        staged_demo = os.path.join(self.cs2_dir, "auto_record_match.dem")
        try:
            shutil.copy2(self.selected_demo_path, staged_demo)
            self.log("Staged demo to CS2 folder: auto_record_match.dem")
        except Exception as e:
            self.log(f"Note staging demo: {e}")

        # Automatically deploy native Panorama HUD & Menu into game/csgo/panorama/
        self.deploy_panorama_hud(silent=True)

        # 2. Deploy auto-exec CFG
        cfg_path = os.path.join(self.cs2_dir, "cfg", "cs2_auto_record.cfg")
        os.makedirs(os.path.dirname(cfg_path), exist_ok=True)
        with open(cfg_path, "w", encoding="utf-8") as f:
            f.write("sv_cheats 1\ncl_drawhud 1\nr_drawviewmodel 1\necho [REPLAY_STUDIO] In-Engine Panorama HUD Active...\n")

        # 3. Launch CS2 in Borderless Windowed mode with loose Panorama asset loading
        port = self.var_netcon_port.get().strip() or "2121"
        cs2_cmd = [
            self.cs2_exe,
            "-insecure",
            "-dev",
            "-novid",
            "-netconport", port,
            "+playdemo", "auto_record_match",
            "+exec", "cs2_auto_record.cfg"
        ]
        if self.var_borderless.get():
            cs2_cmd.extend(["-windowed", "-noborder"])

        self.log(f"Launching CS2 (+playdemo auto_record_match, netcon {port}, native Panorama)...")
        try:
            self.cs2_proc = subprocess.Popen(cs2_cmd)
        except Exception as e:
            self.log(f"Failed to launch CS2: {e}")
            return

        # Monitor CS2 process so companion overlay terminates automatically when game closes
        threading.Thread(target=self._monitor_cs2_process, daemon=True).start()

        # 4. Launch External Overlay only if explicitly requested
        if self.var_launch_external_overlay.get():
            self._start_overlay_process(port)
        else:
            self.log("Native in-engine Panorama HUD & Menu active in CS2! (Zero external overlay clutter)")

    def launch_overlay_only(self):
        port = self.var_netcon_port.get().strip() or "2121"
        self._start_overlay_process(port)

    def _start_overlay_process(self, port: str):
        overlay_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "overlay.py")
        cmd = [sys.executable, overlay_script, "--netcon-port", port]
        if self.selected_demo_path:
            cmd.append(self.selected_demo_path)

        self.log("Starting in-game transparent HUD overlay...")
        try:
            self.overlay_proc = subprocess.Popen(cmd)
            self.log("Overlay running! Press [F1] or [INSERT] in CS2 to toggle in-game settings.")
        except Exception as e:
            self.log(f"Failed to launch overlay: {e}")

    def stop_all(self):
        self.log("Stopping active replay session...")
        if self.overlay_proc:
            try:
                self.overlay_proc.terminate()
                self.log("Overlay terminated.")
            except Exception:
                pass
            self.overlay_proc = None

        if self.cs2_proc:
            try:
                self.cs2_proc.terminate()
                self.log("CS2 process terminated.")
            except Exception:
                pass
            self.cs2_proc = None

    def log(self, msg: str):
        timestamp = time.strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {msg}\n"
        self.txt_console.insert("end", formatted)
        self.txt_console.see("end")

    @staticmethod
    def _get_desktop_path() -> str:
        """Finds the true Windows Desktop directory (handling OneDrive redirection)."""
        if sys.platform == "win32":
            try:
                import winreg
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders"
                )
                val, _ = winreg.QueryValueEx(key, "Desktop")
                expanded = os.path.expandvars(val)
                if os.path.exists(expanded):
                    return expanded
            except Exception:
                pass
        return os.path.expanduser(r"~\Desktop")

    def create_desktop_shortcut(self):
        """Creates a native Windows Desktop shortcut pointing to pythonw launcher.pyw."""
        desktop = self._get_desktop_path()
        app_dir = os.path.dirname(os.path.abspath(__file__))
        pyw_entry = os.path.join(app_dir, "launcher.pyw")
        py_entry = os.path.join(app_dir, "launcher.py")

        python_exe = sys.executable
        pythonw_exe = os.path.join(os.path.dirname(python_exe), "pythonw.exe")
        target_exe = pythonw_exe if os.path.exists(pythonw_exe) else python_exe
        target_script = pyw_entry if os.path.exists(pyw_entry) else py_entry

        shortcut_path = os.path.join(desktop, "CS2 Replay Studio.lnk")

        vbs_script = f'''
Set oWS = WScript.CreateObject("WScript.Shell")
sLinkFile = "{shortcut_path}"
Set oLink = oWS.CreateShortcut(sLinkFile)
oLink.TargetPath = "{target_exe}"
oLink.Arguments = """{target_script}"""
oLink.WorkingDirectory = "{app_dir}"
oLink.Description = "Counter-Strike 2 Sub-Tick Replay Studio // Control Center"
oLink.Save
'''
        try:
            temp_vbs = os.path.join(app_dir, "_mkshortcut.vbs")
            with open(temp_vbs, "w", encoding="utf-8") as f:
                f.write(vbs_script)

            subprocess.run(["cscript", "//nologo", temp_vbs], check=True, creationflags=0x08000000)
            if os.path.exists(temp_vbs):
                os.remove(temp_vbs)

            self.log(f"Desktop shortcut created: {shortcut_path}")
            messagebox.showinfo(
                "Shortcut Created",
                f"Successfully created Desktop Shortcut!\n\nLocation:\n{shortcut_path}\n\n"
                f"You can now launch CS2 Replay Studio directly from your desktop without any .bat files."
            )
        except Exception as e:
            self.log(f"Failed to create desktop shortcut: {e}")
            messagebox.showerror("Shortcut Error", f"Failed to create desktop shortcut:\n{e}")

    def _load_local_version(self) -> Dict[str, Any]:
        """Loads the current local build version and commit hash."""
        v_file = os.path.join(self.app_dir, "version.json")
        if os.path.exists(v_file):
            try:
                with open(v_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        # Fallback to git rev-parse if available in repo
        try:
            res = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=self.app_dir, capture_output=True, text=True, timeout=2)
            if res.returncode == 0 and res.stdout.strip():
                return {"commit_sha": res.stdout.strip(), "version": "1.2.0"}
        except Exception:
            pass
        return {"commit_sha": "0cd56d7", "version": "1.2.0"}

    def check_and_install_updates(self, silent_if_latest: bool = False):
        """Checks GitHub repository for updates and installs them only when a newer version exists."""
        def _worker():
            self.log("Connecting to GitHub to check for updates...")
            api_url = "https://api.github.com/repos/Hanzkii/cs2-replay-overlay/commits/main"
            zip_url = "https://github.com/Hanzkii/cs2-replay-overlay/archive/refs/heads/main.zip"
            headers = {"User-Agent": "CS2-Replay-Studio-Client"}

            try:
                req = urllib.request.Request(api_url, headers=headers)
                with urllib.request.urlopen(req, timeout=10) as resp:
                    commit_data = json.loads(resp.read().decode("utf-8"))

                remote_sha = commit_data.get("sha", "").strip()
                remote_sha_short = remote_sha[:7]
                commit_msg = commit_data.get("commit", {}).get("message", "").split("\n")[0]

                # Check current local version
                local_info = self._load_local_version()
                local_sha = local_info.get("commit_sha", "").strip()

                # If already up to date, inform the user and abort download
                if local_sha and (remote_sha.startswith(local_sha) or local_sha.startswith(remote_sha_short)):
                    self.log(f"CS2 Replay Studio is already up to date (version {remote_sha_short}: '{commit_msg}').")
                    if not silent_if_latest:
                        messagebox.showinfo(
                            "Already Up to Date",
                            f"CS2 Replay Studio is already up to date!\n\n"
                            f"Current Version: {remote_sha_short}\n"
                            f"Latest Commit: {commit_msg}\n\n"
                            f"No updates are needed."
                        )
                    return

                # Newer version detected
                self.log(f"New update available: {local_sha[:7] or 'Unknown'} -> {remote_sha_short} ('{commit_msg}')")

                if not messagebox.askyesno(
                    "Update Available",
                    f"A new update is available!\n\n"
                    f"Current Version: {local_sha[:7] or 'Unknown'}\n"
                    f"Latest Version:  {remote_sha_short}\n\n"
                    f"Release Notes: {commit_msg}\n\n"
                    f"Do you want to download and install this update now?"
                ):
                    self.log("Update postponed by user.")
                    return

                # Download repository archive
                self.log(f"Downloading update {remote_sha_short} from GitHub...")
                req_zip = urllib.request.Request(zip_url, headers=headers)
                with urllib.request.urlopen(req_zip, timeout=20) as resp:
                    zip_data = resp.read()

                # Extract over current directory
                app_dir = self.app_dir
                updated_count = 0
                with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
                    for name in zf.namelist():
                        parts = name.split("/", 1)
                        if len(parts) < 2 or not parts[1]:
                            continue
                        rel_file = parts[1]
                        if rel_file.endswith((".py", ".pyw", ".bat", ".md", ".txt", ".cfg", ".json", ".xml", ".css", ".js")):
                            dest_path = os.path.join(app_dir, rel_file)
                            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                            with open(dest_path, "wb") as f_out:
                                f_out.write(zf.read(name))
                            updated_count += 1

                # Save new version.json locally
                new_version = {
                    "version": "1.2.0",
                    "commit_sha": remote_sha_short,
                    "commit_msg": commit_msg,
                    "updated_at": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                v_file = os.path.join(app_dir, "version.json")
                with open(v_file, "w", encoding="utf-8") as f:
                    json.dump(new_version, f, indent=2)
                self.local_version = new_version

                # Clean cache
                pycache = os.path.join(app_dir, "__pycache__")
                if os.path.exists(pycache):
                    shutil.rmtree(pycache, ignore_errors=True)

                self.log(f"Successfully updated {updated_count} files to version {remote_sha_short}!")

                if messagebox.askyesno(
                    "Update Complete",
                    f"CS2 Replay Studio successfully updated to version {remote_sha_short}!\n\n"
                    f"Commit: {commit_msg}\n\n"
                    f"Do you want to restart the application now?"
                ):
                    self._restart_launcher()

            except Exception as e:
                self.log(f"Update failed: {e}")
                if not silent_if_latest:
                    messagebox.showerror("Update Error", f"Failed to check or apply updates:\n{e}")

        threading.Thread(target=_worker, daemon=True).start()

    def _restart_launcher(self):
        """Restarts the launcher via pythonw or python without batch files."""
        app_dir = os.path.dirname(os.path.abspath(__file__))
        pyw_entry = os.path.join(app_dir, "launcher.pyw")
        py_entry = os.path.join(app_dir, "launcher.py")

        python_exe = sys.executable
        pythonw_exe = os.path.join(os.path.dirname(python_exe), "pythonw.exe")
        target_exe = pythonw_exe if os.path.exists(pythonw_exe) else python_exe
        target_script = pyw_entry if os.path.exists(pyw_entry) else py_entry

        try:
            subprocess.Popen([target_exe, target_script], cwd=app_dir)
            self.root.destroy()
            sys.exit(0)
        except Exception as e:
            self.log(f"Auto-restart failed: {e}")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = ReplayStudioLauncherApp()
    app.run()
