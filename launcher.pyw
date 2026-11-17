#!/usr/bin/env python3
"""
launcher.py - Counter-Strike 2 Replay & Combat Anomaly Navigator Desktop Control Center

A streamlined, high-performance desktop replay analysis station and demo viewer:
  1. Automated CS2 and Steam auto-discovery across all library drives.
  2. Instant .dem match parsing with full player roster extraction and live event indexing.
  3. Automated Combat & Anti-Cheat Anomaly Engine:
     - Aimbot viewangle snap velocity analysis (Δθ > 35°/tick).
     - Sub-tick triggerbot micro-slice timing clustering (< 2.0 ms).
     - Lag compensation desync and backtrack rewind auditing.
  4. 1-Click Netcon Loopback Synchronization:
     - Instantly seeks CS2 to the exact lead-up tick before the action (demo_gototick <tick - lead>).
     - Locks spectator camera directly into the suspect's 1st-person view (spec_mode 1 & spec_player "<player>").
     - Automatically slows down playback (0.25x slow-mo) for effortless visual auditing.
     - Controls playback speed, pause/play, camera modes, and in-engine debug overlays.
  5. Interactive visual timeline scrubber with highlighted audit intervals.

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
from typing import Optional, Dict, List, Any

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from engine_link import CS2Locator, CS2NetconClient
from demo_parser import CS2DemoSummary


class ReplayStudioApp:
    """Desktop Replay Studio & Combat Anomaly Navigator for Counter-Strike 2."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Counter-Strike 2 // Replay & Combat Anomaly Navigator")
        self.root.geometry("1120x800")
        self.root.minsize(960, 680)

        # Dark Cyberpunk / CS2 Palette
        self.bg_dark = "#090d16"
        self.card_bg = "#111827"
        self.panel_bg = "#1e293b"
        self.border_col = "#334155"
        self.accent_cyan = "#38bdf8"
        self.accent_indigo = "#818cf8"
        self.accent_emerald = "#34d399"
        self.accent_coral = "#f43f5e"
        self.accent_amber = "#fbbf24"
        self.text_main = "#f8fafc"
        self.text_muted = "#94a3b8"

        self.root.config(bg=self.bg_dark)

        # State Variables
        self.app_dir = os.path.dirname(os.path.abspath(__file__))
        self.local_version = self._load_local_version()
        self.selected_demo_path: Optional[str] = None
        self.demo_info: Dict[str, Any] = {}
        self.anomalies: List[Dict[str, Any]] = []
        self.filtered_anomalies: List[Dict[str, Any]] = []
        self.analytics: Dict[str, Any] = {}

        self.cs2_exe: Optional[str] = None
        self.cs2_dir: Optional[str] = None
        self.cs2_proc: Optional[subprocess.Popen] = None

        self.var_borderless = tk.BooleanVar(value=True)
        self.var_netcon_port = tk.StringVar(value="2121")

        # Netcon Client
        self.netcon = CS2NetconClient(port=2121)

        # Timeline Scrubber State
        self.current_tick = 0
        self.max_demo_tick = 100000

        # UI Filter Vars
        self.var_filter_category = tk.StringVar(value="All Categories")
        self.var_filter_player = tk.StringVar(value="All Players")
        self.var_filter_severity = tk.StringVar(value="All Severities")
        self.var_filter_search = tk.StringVar(value="")

        # Automated Anomaly Jump & Audit Configuration
        self.var_autojump_on_click = tk.BooleanVar(value=True)
        self.var_leadup_seconds = tk.StringVar(value="1.5s (96 ticks)")
        self.var_slowmo_speed = tk.StringVar(value="0.25x (Super Slow)")
        self.selected_event_tick = 0
        self.selected_event_lead = 0

        # Discover CS2 initially
        self._discover_cs2()

        # Build UI layout
        self._setup_styles()
        self._build_ui()

        # Start periodic background monitor for Netcon & CS2 status
        self._start_engine_poll()

        # Check if demo path passed via command line
        if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
            self.load_demo(sys.argv[1])
        elif self.cs2_dir:
            # Auto-check if auto_record_match.dem exists in csgo dir
            staged = os.path.join(self.cs2_dir, "auto_record_match.dem")
            if os.path.exists(staged):
                self.load_demo(staged)

        self.log("CS2 Replay & Combat Anomaly Navigator initialized.")
        if self.cs2_exe:
            self.log(f"Auto-detected Counter-Strike 2: {os.path.basename(self.cs2_exe)}")
        else:
            self.log("Note: cs2.exe not found automatically. Click 'Locate cs2.exe' to browse.")

    def _discover_cs2(self):
        info = CS2Locator.find_cs2()
        if info:
            self.cs2_exe, self.cs2_dir = info

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "Treeview",
            background="#0d1117",
            foreground=self.text_main,
            fieldbackground="#0d1117",
            rowheight=26,
            font=("Consolas", 9),
            borderwidth=0
        )
        style.configure(
            "Treeview.Heading",
            background=self.card_bg,
            foreground=self.accent_cyan,
            font=("Segoe UI", 9, "bold"),
            relief="flat"
        )
        style.map("Treeview", background=[("selected", "#1e3a8a")], foreground=[("selected", "#ffffff")])

    def _build_ui(self):
        # 1. Top Header Bar
        header = tk.Frame(self.root, bg="#0d1117", height=56, padx=16, pady=8)
        header.pack(fill="x", side="top")

        lbl_title = tk.Label(
            header,
            text="COUNTER-STRIKE 2 // REPLAY & COMBAT ANOMALY NAVIGATOR",
            font=("Segoe UI", 12, "bold"),
            fg=self.accent_cyan,
            bg="#0d1117"
        )
        lbl_title.pack(side="left")

        lbl_sub = tk.Label(
            header,
            text="DEMO VIEWER // NETCON ENGINE LINK",
            font=("Consolas", 8, "bold"),
            fg="#c084fc",
            bg="#2e1065",
            padx=8, pady=2
        )
        lbl_sub.pack(side="left", padx=10)

        self.lbl_netcon_status = tk.Label(
            header,
            text="○ Netcon: Standby",
            font=("Consolas", 9, "bold"),
            fg=self.text_muted,
            bg="#0d1117"
        )
        self.lbl_netcon_status.pack(side="right", padx=(10, 0))

        btn_update = tk.Button(
            header,
            text="🔄 Update Tool",
            font=("Segoe UI", 8, "bold"),
            bg="#1e293b", fg=self.accent_cyan,
            activebackground="#334155", activeforeground="#ffffff",
            relief="flat", padx=8, pady=3,
            cursor="hand2",
            command=self.check_and_install_updates
        )
        btn_update.pack(side="right", padx=4)

        btn_shortcut = tk.Button(
            header,
            text="📌 Desktop Icon",
            font=("Segoe UI", 8, "bold"),
            bg="#1e293b", fg=self.accent_emerald,
            activebackground="#334155", activeforeground="#ffffff",
            relief="flat", padx=8, pady=3,
            cursor="hand2",
            command=self.create_desktop_shortcut
        )
        btn_shortcut.pack(side="right", padx=4)

        # 2. Match Ingestion & CS2 Engine Controls (Top Deck)
        top_deck = tk.Frame(self.root, bg=self.bg_dark, padx=14, pady=6)
        top_deck.pack(fill="x")

        # Left Card: Demo Ingestion
        self._build_ingestion_card(top_deck)

        # Right Card: CS2 Launch & Engine Link
        self._build_engine_card(top_deck)

        # 3. Dedicated CS2 Netcon Playback Transport Bar
        self._build_transport_bar()

        # 4. Interactive Timeline Scrubber Bar
        self._build_timeline_scrubber()

        # 5. Dedicated Full-Height Anomaly & Combat Event Navigator
        main_container = tk.Frame(self.root, bg=self.card_bg, padx=12, pady=8, relief="groove", bd=1)
        main_container.pack(fill="both", expand=True, padx=14, pady=(4, 4))

        self._build_anomaly_navigator(main_container)

        # 6. Bottom Diagnostics Console
        self._build_console()

    def _build_ingestion_card(self, parent):
        card = tk.LabelFrame(
            parent,
            text=" 1. MATCH RECORDING (.DEM) INGESTION ",
            font=("Consolas", 8, "bold"),
            bg=self.card_bg, fg=self.accent_indigo,
            padx=12, pady=6, relief="groove", bd=1
        )
        card.pack(side="left", fill="both", expand=True, padx=(0, 6))

        top_row = tk.Frame(card, bg=self.card_bg)
        top_row.pack(fill="x", pady=(0, 4))

        btn_browse = tk.Button(
            top_row,
            text="📁 Browse .dem File...",
            font=("Segoe UI", 9, "bold"),
            bg="#2563eb", fg="#ffffff",
            activebackground="#3b82f6", activeforeground="#ffffff",
            relief="flat", padx=10, pady=3,
            cursor="hand2",
            command=self.browse_demo_file
        )
        btn_browse.pack(side="left")

        self.lbl_demo_file = tk.Label(
            top_row,
            text="No demo loaded. (Click Browse or drag & drop .dem)",
            font=("Consolas", 9),
            fg=self.text_muted,
            bg=self.card_bg,
            anchor="w"
        )
        self.lbl_demo_file.pack(side="left", padx=10, fill="x", expand=True)

        # Meta pills row
        meta_row = tk.Frame(card, bg="#0d1117", padx=8, pady=4, relief="ridge", bd=1)
        meta_row.pack(fill="x")

        self.lbl_meta_map = tk.Label(meta_row, text="Map: --", font=("Consolas", 8, "bold"), fg=self.accent_cyan, bg="#0d1117")
        self.lbl_meta_map.pack(side="left", padx=6)

        self.lbl_meta_tick = tk.Label(meta_row, text="Tickrate: --", font=("Consolas", 8), fg=self.accent_emerald, bg="#0d1117")
        self.lbl_meta_tick.pack(side="left", padx=6)

        self.lbl_meta_dur = tk.Label(meta_row, text="Duration: --", font=("Consolas", 8), fg=self.text_main, bg="#0d1117")
        self.lbl_meta_dur.pack(side="left", padx=6)

        self.lbl_meta_players = tk.Label(meta_row, text="Players: --", font=("Consolas", 8), fg=self.accent_amber, bg="#0d1117")
        self.lbl_meta_players.pack(side="left", padx=6)

        self.lbl_meta_events = tk.Label(meta_row, text="Events: --", font=("Consolas", 8, "bold"), fg=self.accent_coral, bg="#0d1117")
        self.lbl_meta_events.pack(side="left", padx=6)

    def _build_engine_card(self, parent):
        card = tk.LabelFrame(
            parent,
            text=" 2. COUNTER-STRIKE 2 ENGINE LINK ",
            font=("Consolas", 8, "bold"),
            bg=self.card_bg, fg=self.accent_indigo,
            padx=12, pady=6, relief="groove", bd=1
        )
        card.pack(side="right", fill="both", expand=True, padx=(6, 0))

        top_row = tk.Frame(card, bg=self.card_bg)
        top_row.pack(fill="x", pady=(0, 4))

        target_text = os.path.basename(self.cs2_exe) if self.cs2_exe else "cs2.exe Not Located"
        self.lbl_cs2_target = tk.Label(
            top_row,
            text=f"Engine: {target_text}",
            font=("Consolas", 9, "bold"),
            fg=self.accent_emerald if self.cs2_exe else self.accent_coral,
            bg=self.card_bg
        )
        self.lbl_cs2_target.pack(side="left")

        btn_locate = tk.Button(
            top_row,
            text="Locate cs2.exe...",
            font=("Segoe UI", 8),
            bg="#1e293b", fg="#cbd5e1",
            relief="flat", padx=6, pady=2,
            cursor="hand2",
            command=self.browse_cs2_exe
        )
        btn_locate.pack(side="right")

        opts_row = tk.Frame(card, bg=self.card_bg)
        opts_row.pack(fill="x")

        chk_border = tk.Checkbutton(
            opts_row,
            text="Borderless (-windowed -noborder)",
            variable=self.var_borderless,
            font=("Segoe UI", 8),
            bg=self.card_bg, fg=self.text_main,
            selectcolor="#090d16", activebackground=self.card_bg, activeforeground=self.text_main
        )
        chk_border.pack(side="left")

        tk.Label(opts_row, text="Port:", font=("Segoe UI", 8), fg=self.text_muted, bg=self.card_bg).pack(side="left", padx=(8, 2))
        ent_port = tk.Entry(opts_row, textvariable=self.var_netcon_port, width=5, bg="#0d1117", fg=self.accent_cyan, insertbackground="#fff", font=("Consolas", 8))
        ent_port.pack(side="left")

        self.btn_launch_cs2 = tk.Button(
            opts_row,
            text="▶ LAUNCH CS2 & SYNC",
            font=("Segoe UI", 9, "bold"),
            bg="#059669", fg="#ffffff",
            activebackground="#10b981", activeforeground="#ffffff",
            relief="flat", padx=10, pady=2,
            cursor="hand2",
            command=self.launch_cs2_replay
        )
        self.btn_launch_cs2.pack(side="right", padx=(6, 0))

        btn_stop = tk.Button(
            opts_row,
            text="⏹ Stop",
            font=("Segoe UI", 8, "bold"),
            bg="#450a0a", fg="#fca5a5",
            relief="flat", padx=6, pady=2,
            cursor="hand2",
            command=self.stop_cs2
        )
        btn_stop.pack(side="right")

    def _build_transport_bar(self):
        """Dedicated Netcon engine transport bar to control demo playback in CS2."""
        bar = tk.Frame(self.root, bg="#0f172a", padx=14, pady=5, relief="ridge", bd=1)
        bar.pack(fill="x", padx=14, pady=(2, 2))

        # Playback navigation
        lbl_transport = tk.Label(bar, text="NETCON CONTROLS:", font=("Consolas", 8, "bold"), fg=self.accent_cyan, bg="#0f172a")
        lbl_transport.pack(side="left", padx=(0, 8))

        btn_r_back = tk.Button(bar, text="⏮ -1 Round", font=("Segoe UI", 8), bg="#1e293b", fg=self.text_main, relief="flat", padx=6, pady=1, cursor="hand2",
                               command=lambda: self.seek_relative_ticks(-64 * 115))
        btn_r_back.pack(side="left", padx=2)

        btn_t_back = tk.Button(bar, text="⏪ -64 Ticks", font=("Segoe UI", 8), bg="#1e293b", fg=self.text_main, relief="flat", padx=6, pady=1, cursor="hand2",
                               command=lambda: self.seek_relative_ticks(-64))
        btn_t_back.pack(side="left", padx=2)

        self.btn_play_pause = tk.Button(bar, text="⏯ Play / Pause", font=("Segoe UI", 8, "bold"), bg="#2563eb", fg="#ffffff", relief="flat", padx=10, pady=1, cursor="hand2",
                                        command=self.toggle_engine_pause)
        self.btn_play_pause.pack(side="left", padx=4)

        btn_t_fwd = tk.Button(bar, text="+64 Ticks ⏩", font=("Segoe UI", 8), bg="#1e293b", fg=self.text_main, relief="flat", padx=6, pady=1, cursor="hand2",
                              command=lambda: self.seek_relative_ticks(64))
        btn_t_fwd.pack(side="left", padx=2)

        btn_r_fwd = tk.Button(bar, text="+1 Round ⏭", font=("Segoe UI", 8), bg="#1e293b", fg=self.text_main, relief="flat", padx=6, pady=1, cursor="hand2",
                              command=lambda: self.seek_relative_ticks(64 * 115))
        btn_r_fwd.pack(side="left", padx=2)

        # Timescale selector
        tk.Label(bar, text="Speed:", font=("Segoe UI", 8), fg=self.text_muted, bg="#0f172a").pack(side="left", padx=(10, 4))
        for speed in (0.25, 0.5, 1.0, 2.0, 4.0):
            btn_spd = tk.Button(bar, text=f"{speed}x", font=("Consolas", 8), bg="#1e293b", fg=self.accent_cyan if speed == 1.0 else self.text_muted,
                                relief="flat", padx=4, pady=1, cursor="hand2", command=lambda s=speed: self.set_engine_timescale(s))
            btn_spd.pack(side="left", padx=1)

        # Camera mode selector
        tk.Label(bar, text="Cam:", font=("Segoe UI", 8), fg=self.text_muted, bg="#0f172a").pack(side="left", padx=(10, 4))
        btn_cam1 = tk.Button(bar, text="1st Person", font=("Segoe UI", 8), bg="#1e293b", fg=self.text_main, relief="flat", padx=6, pady=1, cursor="hand2",
                             command=lambda: self.set_camera_perspective(1))
        btn_cam1.pack(side="left", padx=2)

        btn_cam2 = tk.Button(bar, text="Chase", font=("Segoe UI", 8), bg="#1e293b", fg=self.text_main, relief="flat", padx=6, pady=1, cursor="hand2",
                             command=lambda: self.set_camera_perspective(2))
        btn_cam2.pack(side="left", padx=2)

        btn_cam6 = tk.Button(bar, text="Free Roam", font=("Segoe UI", 8), bg="#1e293b", fg=self.text_main, relief="flat", padx=6, pady=1, cursor="hand2",
                             command=lambda: self.set_camera_perspective(6))
        btn_cam6.pack(side="left", padx=2)

        # Debug overlays toggle in CS2
        btn_lagcomp = tk.Button(bar, text="Hitboxes [sv_showlagcomp]", font=("Segoe UI", 8), bg="#312e81", fg="#c7d2fe", relief="flat", padx=6, pady=1, cursor="hand2",
                                command=self.toggle_lagcomp_debug)
        btn_lagcomp.pack(side="right", padx=2)

        btn_impacts = tk.Button(bar, text="Impacts [sv_showimpacts]", font=("Segoe UI", 8), bg="#312e81", fg="#c7d2fe", relief="flat", padx=6, pady=1, cursor="hand2",
                                command=self.toggle_impacts_debug)
        btn_impacts.pack(side="right", padx=2)

    def _build_timeline_scrubber(self):
        """Interactive visual timeline scrubber bar showing event markers and clickable seeking."""
        frame = tk.Frame(self.root, bg=self.bg_dark, padx=14, pady=2)
        frame.pack(fill="x")

        lbl_row = tk.Frame(frame, bg=self.bg_dark)
        lbl_row.pack(fill="x")

        tk.Label(lbl_row, text="MATCH TIMELINE SCRUBBER (Click anywhere to seek CS2):", font=("Consolas", 8, "bold"), fg=self.text_muted, bg=self.bg_dark).pack(side="left")
        self.lbl_scrub_pos = tk.Label(lbl_row, text="Tick 0 (00:00) / 100000", font=("Consolas", 8, "bold"), fg=self.accent_cyan, bg=self.bg_dark)
        self.lbl_scrub_pos.pack(side="right")

        self.canvas_timeline = tk.Canvas(frame, height=32, bg="#0d1117", highlightthickness=1, highlightbackground=self.border_col, cursor="hand2")
        self.canvas_timeline.pack(fill="x", pady=2)

        self.canvas_timeline.bind("<Button-1>", self._on_timeline_click)
        self.canvas_timeline.bind("<B1-Motion>", self._on_timeline_click)
        self.canvas_timeline.bind("<Configure>", lambda e: self.draw_timeline())

    def draw_timeline(self):
        """Redraws the timeline canvas with round dividers, event ticks, and scrubber needle."""
        c = self.canvas_timeline
        c.delete("all")
        w = c.winfo_width()
        h = c.winfo_height()
        if w < 10 or self.max_demo_tick <= 0:
            return

        # Background track
        c.create_rectangle(0, 0, w, h, fill="#0b0f19", outline="")

        # Draw round boundaries (~64 ticks * 115 seconds = 7360 ticks per round)
        ticks_per_round = 7360
        r_num = 1
        cur_r_tick = 24000
        while cur_r_tick < self.max_demo_tick:
            rx = int((cur_r_tick / self.max_demo_tick) * w)
            c.create_line(rx, 0, rx, h, fill="#1f2937", width=1)
            c.create_text(rx + 2, 8, text=f"R{r_num}", anchor="w", fill="#475569", font=("Consolas", 7))
            cur_r_tick += ticks_per_round
            r_num += 1

        # Draw anomaly & combat markers
        for event in self.anomalies:
            t = event.get("tick", 0)
            ex = int((t / self.max_demo_tick) * w)
            cat = event.get("category", "")
            sev = event.get("severity", "")

            if sev == "CRITICAL" or cat in ("AIMBOT_SNAP", "SUBTICK_TRIGGER"):
                c.create_polygon(ex - 4, h - 2, ex + 4, h - 2, ex, h - 12, fill=self.accent_coral, outline="")
            elif sev == "SUSPICIOUS" or cat == "DESYNC_BACKTRACK":
                c.create_polygon(ex - 3, h - 2, ex + 3, h - 2, ex, h - 9, fill=self.accent_amber, outline="")
            elif cat == "COMBAT_KILL":
                c.create_oval(ex - 2, 4, ex + 2, 8, fill="#ef4444", outline="")
            else:
                c.create_line(ex, 12, ex, h - 12, fill="#0284c7", width=1)

        # Highlight active audit window (lead-up to impact)
        if self.selected_event_tick > 0 and self.selected_event_lead > 0 and self.max_demo_tick > 0:
            lx = int((self.selected_event_lead / self.max_demo_tick) * w)
            ix = int((self.selected_event_tick / self.max_demo_tick) * w)
            if ix > lx:
                c.create_rectangle(lx, 2, ix, h - 2, fill="#1e3a8a", outline="#3b82f6", width=1)
                c.create_text(ix - 2, 7, text="⚡ SNAP", fill="#f87171", font=("Consolas", 7, "bold"), anchor="e")

        # Scrubber needle
        nx = int((self.current_tick / self.max_demo_tick) * w)
        c.create_line(nx, 0, nx, h, fill="#38bdf8", width=2)
        c.create_polygon(nx - 5, 0, nx + 5, 0, nx, 7, fill="#38bdf8", outline="")

    def _on_timeline_click(self, event):
        w = self.canvas_timeline.winfo_width()
        if w <= 0 or self.max_demo_tick <= 0:
            return
        frac = max(0.0, min(1.0, event.x / w))
        target_tick = int(frac * self.max_demo_tick)
        self.seek_to_tick(target_tick)

    def seek_to_tick(self, target_tick: int, suspect_to_spec: Optional[str] = None):
        """Sends Netcon command to seek CS2 and updates UI needle."""
        self.current_tick = target_tick
        total_secs = target_tick // 64
        mins = total_secs // 60
        secs = total_secs % 60
        self.lbl_scrub_pos.config(text=f"Tick {target_tick:06d} ({mins:02d}:{secs:02d}) / {self.max_demo_tick}")
        self.draw_timeline()

        # Netcon dispatch
        if self.netcon.is_connected() or self.netcon.try_connect():
            self.netcon.goto_tick(target_tick)
            if suspect_to_spec:
                self.netcon.spec_player(suspect_to_spec)
            self.log(f"Seeking CS2 -> Tick {target_tick:06d} ({mins:02d}:{secs:02d})" + (f" | Spectating {suspect_to_spec}" if suspect_to_spec else ""))
        else:
            self.log(f"Target Tick {target_tick:06d} set (CS2 Netcon not yet connected).")

    def seek_relative_ticks(self, delta: int):
        target = max(0, min(self.max_demo_tick, self.current_tick + delta))
        self.seek_to_tick(target)

    def toggle_engine_pause(self):
        if self.netcon.is_connected() or self.netcon.try_connect():
            self.netcon.toggle_pause()
            self.log("Netcon -> demo_togglepause executed.")

    def set_engine_timescale(self, scale: float):
        if self.netcon.is_connected() or self.netcon.try_connect():
            self.netcon.set_timescale(scale)
            self.log(f"Netcon -> demo_timescale {scale:.2f}")

    def set_camera_perspective(self, mode: int):
        modes = {1: "First Person", 2: "Chase Cam", 6: "Free Roam"}
        if self.netcon.is_connected() or self.netcon.try_connect():
            self.netcon.spec_mode(mode)
            self.log(f"Netcon -> spec_mode {mode} ({modes.get(mode, 'Unknown')})")

    def toggle_lagcomp_debug(self):
        if self.netcon.is_connected() or self.netcon.try_connect():
            self.netcon.toggle_lag_compensation_box()
            self.log("Netcon -> toggle sv_showlagcompensation 0 1")

    def toggle_impacts_debug(self):
        if self.netcon.is_connected() or self.netcon.try_connect():
            self.netcon.toggle_bullet_impacts()
            self.log("Netcon -> toggle sv_showimpacts 0 1")

    # =========================================================================
    # DEDICATED FULL-HEIGHT COMBAT & ANOMALY NAVIGATOR
    # =========================================================================
    def _build_anomaly_navigator(self, container):
        # Filter bar
        filter_bar = tk.Frame(container, bg=self.card_bg, pady=4)
        filter_bar.pack(fill="x")

        tk.Label(filter_bar, text="Category:", font=("Segoe UI", 9, "bold"), fg=self.accent_cyan, bg=self.card_bg).pack(side="left")
        self.cb_filter_cat = ttk.Combobox(
            filter_bar,
            textvariable=self.var_filter_category,
            values=["All Categories", "Aimbot Snaps (Δθ > 35°)", "Sub-Tick Triggerbots (w < 2ms)", "Backtrack & Desync (> 4u)", "Combat Kills & Hits"],
            state="readonly",
            width=26
        )
        self.cb_filter_cat.pack(side="left", padx=(4, 10))
        self.cb_filter_cat.bind("<<ComboboxSelected>>", lambda e: self.apply_anomaly_filters())

        tk.Label(filter_bar, text="Suspect:", font=("Segoe UI", 9, "bold"), fg=self.accent_cyan, bg=self.card_bg).pack(side="left")
        self.cb_filter_player = ttk.Combobox(
            filter_bar,
            textvariable=self.var_filter_player,
            values=["All Players"],
            state="readonly",
            width=16
        )
        self.cb_filter_player.pack(side="left", padx=(4, 10))
        self.cb_filter_player.bind("<<ComboboxSelected>>", lambda e: self.apply_anomaly_filters())

        tk.Label(filter_bar, text="Severity:", font=("Segoe UI", 9, "bold"), fg=self.accent_cyan, bg=self.card_bg).pack(side="left")
        self.cb_filter_sev = ttk.Combobox(
            filter_bar,
            textvariable=self.var_filter_severity,
            values=["All Severities", "CRITICAL Only", "SUSPICIOUS Only", "INFO Only"],
            state="readonly",
            width=15
        )
        self.cb_filter_sev.pack(side="left", padx=(4, 10))
        self.cb_filter_sev.bind("<<ComboboxSelected>>", lambda e: self.apply_anomaly_filters())

        tk.Label(filter_bar, text="Search:", font=("Segoe UI", 9), fg=self.text_muted, bg=self.card_bg).pack(side="left")
        ent_search = tk.Entry(filter_bar, textvariable=self.var_filter_search, width=14, bg="#0d1117", fg=self.accent_cyan, insertbackground="#fff", font=("Consolas", 9))
        ent_search.pack(side="left", padx=4)
        ent_search.bind("<KeyRelease>", lambda e: self.apply_anomaly_filters())

        # Table frame
        tbl_frame = tk.Frame(container, bg=self.card_bg)
        tbl_frame.pack(fill="both", expand=True, pady=6)

        columns = ("tick", "round", "time", "severity", "player", "category", "weapon", "metrics")
        self.tree_anomalies = ttk.Treeview(tbl_frame, columns=columns, show="headings", selectmode="browse")

        self.tree_anomalies.heading("tick", text="Tick")
        self.tree_anomalies.heading("round", text="Round")
        self.tree_anomalies.heading("time", text="Time")
        self.tree_anomalies.heading("severity", text="Severity")
        self.tree_anomalies.heading("player", text="Suspect / Player")
        self.tree_anomalies.heading("category", text="Combat Event / Anomaly Category")
        self.tree_anomalies.heading("weapon", text="Weapon")
        self.tree_anomalies.heading("metrics", text="Telemetry & Diagnostic Metrics")

        self.tree_anomalies.column("tick", width=80, anchor="center")
        self.tree_anomalies.column("round", width=60, anchor="center")
        self.tree_anomalies.column("time", width=70, anchor="center")
        self.tree_anomalies.column("severity", width=95, anchor="center")
        self.tree_anomalies.column("player", width=120, anchor="w")
        self.tree_anomalies.column("category", width=220, anchor="w")
        self.tree_anomalies.column("weapon", width=95, anchor="w")
        self.tree_anomalies.column("metrics", width=330, anchor="w")

        tree_scroll = ttk.Scrollbar(tbl_frame, orient="vertical", command=self.tree_anomalies.yview)
        self.tree_anomalies.configure(yscrollcommand=tree_scroll.set)

        self.tree_anomalies.pack(side="left", fill="both", expand=True)
        tree_scroll.pack(side="right", fill="y")

        # Color tags
        self.tree_anomalies.tag_configure("CRITICAL", foreground="#f87171", background="#260b0b")
        self.tree_anomalies.tag_configure("SUSPICIOUS", foreground="#fde047", background="#261e0b")
        self.tree_anomalies.tag_configure("INFO", foreground="#67e8f9")

        self.tree_anomalies.bind("<<TreeviewSelect>>", self._on_table_row_select)
        self.tree_anomalies.bind("<Double-1>", lambda e: self.jump_selected_anomaly())

        # Action bar under table
        act_bar = tk.Frame(container, bg=self.card_bg, pady=6)
        act_bar.pack(fill="x")

        # Top row: Jump button, Lead-Up combo, Slow-mo combo, and Auto-Jump toggle
        param_row = tk.Frame(act_bar, bg=self.card_bg)
        param_row.pack(fill="x", pady=(0, 4))

        self.btn_jump_event = tk.Button(
            param_row,
            text="🎯  JUMP & AUDIT (1ST PERSON // SLOW-MO)",
            font=("Segoe UI", 10, "bold"),
            bg="#2563eb", fg="#ffffff",
            activebackground="#3b82f6", activeforeground="#ffffff",
            relief="flat", padx=14, pady=5,
            cursor="hand2",
            command=self.jump_selected_anomaly
        )
        self.btn_jump_event.pack(side="left")

        btn_resume_normal = tk.Button(
            param_row,
            text="▶ Resume 1.0x",
            font=("Segoe UI", 9, "bold"),
            bg="#1e293b", fg=self.accent_emerald,
            activebackground="#334155", activeforeground="#ffffff",
            relief="flat", padx=10, pady=5,
            cursor="hand2",
            command=lambda: self.set_engine_timescale(1.0)
        )
        btn_resume_normal.pack(side="left", padx=(6, 12))

        chk_autojump = tk.Checkbutton(
            param_row,
            text="Auto-Jump on Click",
            variable=self.var_autojump_on_click,
            font=("Segoe UI", 9, "bold"),
            bg=self.card_bg, fg=self.accent_cyan,
            selectcolor="#090d16", activebackground=self.card_bg, activeforeground=self.accent_cyan
        )
        chk_autojump.pack(side="left", padx=(0, 10))

        tk.Label(param_row, text="Lead-Up:", font=("Segoe UI", 9), fg=self.text_muted, bg=self.card_bg).pack(side="left")
        self.cb_leadup = ttk.Combobox(
            param_row,
            textvariable=self.var_leadup_seconds,
            values=["0.5s (32 ticks)", "1.0s (64 ticks)", "1.5s (96 ticks)", "2.0s (128 ticks)", "2.5s (160 ticks)"],
            state="readonly",
            width=15
        )
        self.cb_leadup.pack(side="left", padx=(4, 10))

        tk.Label(param_row, text="Slow-Mo Speed:", font=("Segoe UI", 9), fg=self.text_muted, bg=self.card_bg).pack(side="left")
        self.cb_slowmo = ttk.Combobox(
            param_row,
            textvariable=self.var_slowmo_speed,
            values=["0.20x (Extreme)", "0.25x (Super Slow)", "0.35x (Smooth Slow)", "0.50x (Half Speed)", "1.00x (Normal)"],
            state="readonly",
            width=18
        )
        self.cb_slowmo.pack(side="left", padx=(4, 0))

        # Bottom row: Informative live status text
        detail_row = tk.Frame(act_bar, bg=self.card_bg)
        detail_row.pack(fill="x")

        self.lbl_selected_detail = tk.Label(
            detail_row,
            text="Click any combat event row to jump ~1.5s before the action directly into the player's 1st-person view in slow motion.",
            font=("Consolas", 9),
            fg=self.accent_emerald,
            bg=self.card_bg,
            anchor="w"
        )
        self.lbl_selected_detail.pack(fill="x", pady=(2, 0))

    def _on_table_row_select(self, event=None):
        if self.var_autojump_on_click.get():
            self.jump_selected_anomaly()
        else:
            sel = self.tree_anomalies.selection()
            if sel:
                item = self.tree_anomalies.item(sel[0])
                vals = item.get("values", [])
                if vals:
                    tick = int(vals[0])
                    player = vals[4]
                    cat = vals[5]
                    self.lbl_selected_detail.config(
                        text=f"Selected: {player} ({cat}) @ Tick {tick:06d}. Click 'JUMP & AUDIT' to spectate in 1st person.",
                        fg=self.accent_cyan
                    )

    def apply_anomaly_filters(self):
        """Filters anomaly list and populates Treeview."""
        cat_filter = self.var_filter_category.get()
        p_filter = self.var_filter_player.get()
        sev_filter = self.var_filter_severity.get()
        query = self.var_filter_search.get().lower().strip()

        self.tree_anomalies.delete(*self.tree_anomalies.get_children())
        filtered = []

        for e in self.anomalies:
            cat = e.get("category", "")
            sev = e.get("severity", "")
            player = e.get("player", "")

            # Category
            if cat_filter == "Aimbot Snaps (Δθ > 35°)" and cat != "AIMBOT_SNAP":
                continue
            elif cat_filter == "Sub-Tick Triggerbots (w < 2ms)" and cat != "SUBTICK_TRIGGER":
                continue
            elif cat_filter == "Backtrack & Desync (> 4u)" and cat != "DESYNC_BACKTRACK":
                continue
            elif cat_filter == "Combat Kills & Hits" and cat not in ("COMBAT_KILL", "COMBAT_HIT"):
                continue

            # Player
            if p_filter != "All Players" and player != p_filter:
                continue

            # Severity
            if sev_filter == "CRITICAL Only" and sev != "CRITICAL":
                continue
            elif sev_filter == "SUSPICIOUS Only" and sev != "SUSPICIOUS":
                continue
            elif sev_filter == "INFO Only" and sev != "INFO":
                continue

            # Query
            if query:
                full_text = f"{player} {cat} {e.get('weapon', '')} {e.get('metric', '')}".lower()
                if query not in full_text:
                    continue

            filtered.append(e)
            row_id = f"evt_{e.get('tick')}_{len(filtered)}"
            self.tree_anomalies.insert(
                "",
                "end",
                iid=row_id,
                values=(
                    f"{e.get('tick', 0):06d}",
                    f"R{e.get('round', 1)}",
                    e.get("time_str", "00:00"),
                    sev,
                    player,
                    cat,
                    e.get("weapon", ""),
                    e.get("metric", "")
                ),
                tags=(sev,)
            )

        self.filtered_anomalies = filtered

    def jump_selected_anomaly(self):
        sel = self.tree_anomalies.selection()
        if not sel:
            messagebox.showinfo("Select Event", "Please select an anomaly row in the table first.")
            return

        item = self.tree_anomalies.item(sel[0])
        vals = item.get("values", [])
        if not vals:
            return

        tick = int(vals[0])
        player = vals[4]
        category = vals[5]
        weapon = vals[6]

        # Parse lead-up ticks
        leadup_str = self.var_leadup_seconds.get()
        lead_ticks = 96
        if "32" in leadup_str: lead_ticks = 32
        elif "64" in leadup_str: lead_ticks = 64
        elif "96" in leadup_str: lead_ticks = 96
        elif "128" in leadup_str: lead_ticks = 128
        elif "160" in leadup_str: lead_ticks = 160

        # Parse slowmo speed
        slowmo_str = self.var_slowmo_speed.get()
        timescale = 0.25
        if "0.20" in slowmo_str: timescale = 0.20
        elif "0.25" in slowmo_str: timescale = 0.25
        elif "0.35" in slowmo_str: timescale = 0.35
        elif "0.50" in slowmo_str: timescale = 0.50
        elif "1.00" in slowmo_str: timescale = 1.00

        lead_tick = max(0, tick - lead_ticks)
        lead_sec = round(lead_ticks / 64.0, 2)

        # Update visual timeline state
        self.current_tick = lead_tick
        self.selected_event_tick = tick
        self.selected_event_lead = lead_tick
        self.draw_timeline()

        # Update position readout
        total_secs = lead_tick // 64
        mins = total_secs // 60
        secs = total_secs % 60
        self.lbl_scrub_pos.config(text=f"Tick {lead_tick:06d} ({mins:02d}:{secs:02d}) / {self.max_demo_tick}")

        # Dispatch reinforced Netcon sequence (goto lead tick -> 1st person -> spectate -> slow motion)
        if self.netcon.is_connected() or self.netcon.try_connect():
            self.netcon.jump_and_inspect(tick=tick, player_name=player, lead_ticks=lead_ticks, timescale=timescale)
            msg = f"🎯 Jumped: {player} (1st Person) | Lead: -{lead_sec}s (Tick {lead_tick:06d}) -> Action @ Tick {tick:06d} | Speed: {timescale}x"
            self.log(msg)
            self.lbl_selected_detail.config(text=msg, fg=self.accent_emerald)
        else:
            msg = f"Target Tick {lead_tick:06d} set (Action @ {tick:06d}). Netcon not connected yet."
            self.log(msg)
            self.lbl_selected_detail.config(text=msg, fg=self.accent_amber)

    # =========================================================================
    # CONSOLE & ENGINE LINK BACKGROUND THREADS
    # =========================================================================
    def _build_console(self):
        frame = tk.Frame(self.root, bg="#030712", padx=14, pady=4)
        frame.pack(fill="x", side="bottom")

        tk.Label(frame, text="LIVE REPLAY STUDIO DIAGNOSTICS & TELEMETRY CONSOLE:", font=("Consolas", 8, "bold"), fg="#64748b", bg="#030712").pack(anchor="w")

        self.txt_console = tk.Text(
            frame,
            height=3,
            bg="#030712",
            fg=self.accent_cyan,
            font=("Consolas", 8),
            insertbackground="#ffffff",
            relief="flat",
            wrap="word"
        )
        self.txt_console.pack(fill="x", expand=True)

    def log(self, msg: str):
        ts = time.strftime("%H:%M:%S")
        self.txt_console.insert("end", f"[{ts}] {msg}\n")
        self.txt_console.see("end")

    def _start_engine_poll(self):
        """Polls Netcon link every 1.5s to maintain live connection status."""
        def _poll_loop():
            while True:
                time.sleep(1.5)
                is_conn = self.netcon.is_connected()
                if not is_conn and self.cs2_proc and self.cs2_proc.poll() is None:
                    self.netcon.try_connect()
                    is_conn = self.netcon.is_connected()

                status_txt = "● Netcon: Connected (2121)" if is_conn else "○ Netcon: Standby"
                status_col = self.accent_emerald if is_conn else self.text_muted
                self.root.after(0, lambda: self.lbl_netcon_status.config(text=status_txt, fg=status_col))

        threading.Thread(target=_poll_loop, daemon=True).start()

    # =========================================================================
    # DEMO INGESTION & LAUNCHER ACTIONS
    # =========================================================================
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
        self.log(f"Ingesting demo: {os.path.basename(self.selected_demo_path)}")

        info = CS2DemoSummary.inspect_file(self.selected_demo_path)
        self.demo_info = info

        if info.get("valid"):
            map_name = info.get("map_name", "Unknown")
            tickrate = info.get("server_tickrate", 64.0)
            dur_str = info.get("duration_str", "00:00")
            players = info.get("players", [])
            max_t = info.get("max_tick", 100000)

            self.max_demo_tick = max_t if max_t > 1000 else 100000

            self.lbl_meta_map.config(text=f"Map: {map_name}")
            self.lbl_meta_tick.config(text=f"Tickrate: {tickrate} Hz")
            self.lbl_meta_dur.config(text=f"Duration: {dur_str}")
            self.lbl_meta_players.config(text=f"Players: {len(players)}")

            # Update comboboxes
            p_values = ["All Players"] + players
            self.cb_filter_player["values"] = p_values

            # Run genuine live combat event scan
            events, analytics = CS2DemoSummary.scan_anomalies(self.selected_demo_path, max_events=120)
            self.anomalies = events
            self.analytics = analytics

            self.lbl_meta_events.config(text=f"Events: {len(events)}")
            self.log(f"Scan complete: {len(events)} live combat events indexed (Snaps: {analytics.get('snaps_count')}, Triggers: {analytics.get('trigger_count')}, Desyncs: {analytics.get('desync_count')})")

            self.apply_anomaly_filters()
            self.draw_timeline()
        else:
            self.log(f"Error reading demo: {info.get('error', 'Invalid format')}")

    def browse_cs2_exe(self):
        f = filedialog.askopenfilename(
            title="Locate cs2.exe",
            filetypes=[("CS2 Executable", "cs2.exe"), ("All Files", "*.*")]
        )
        if f and os.path.exists(f):
            self.cs2_exe = os.path.normpath(f)
            self.cs2_dir = os.path.normpath(os.path.join(os.path.dirname(f), "..", "..", "csgo"))
            self.lbl_cs2_target.config(text=f"Engine: {os.path.basename(self.cs2_exe)}", fg=self.accent_emerald)
            self.log(f"Updated CS2 path: {os.path.basename(self.cs2_exe)}")

    def launch_cs2_replay(self):
        if not self.selected_demo_path or not os.path.exists(self.selected_demo_path):
            messagebox.showwarning("No Demo Selected", "Please select a .dem match recording first.")
            return

        if not self.cs2_exe or not os.path.exists(self.cs2_exe):
            messagebox.showerror("CS2 Not Found", "Counter-Strike 2 executable was not found. Please click 'Locate cs2.exe'.")
            return

        threading.Thread(target=self._launch_worker, daemon=True).start()

    def _launch_worker(self):
        self.log("Preparing Counter-Strike 2 replay playback session...")

        # 1. Stage demo to CS2 game folder
        staged_demo = os.path.join(self.cs2_dir, "auto_record_match.dem")
        if not os.path.exists(staged_demo) or os.path.getsize(staged_demo) != os.path.getsize(self.selected_demo_path):
            try:
                shutil.copy2(self.selected_demo_path, staged_demo)
                self.log("Staged demo to CS2 directory: auto_record_match.dem")
            except Exception as e:
                self.log(f"Note staging demo: {e}")

        # 2. Deploy auto-exec CFG
        cfg_path = os.path.join(self.cs2_dir, "cfg", "cs2_auto_record.cfg")
        os.makedirs(os.path.dirname(cfg_path), exist_ok=True)
        with open(cfg_path, "w", encoding="utf-8") as f:
            f.write("sv_cheats 1\ncl_drawhud 1\nr_drawviewmodel 1\necho [REPLAY_STUDIO] Netcon Live Loopback Link Active...\n")

        # 3. Launch CS2 in Borderless Windowed mode with Netcon loopback
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

        self.log(f"Launching CS2 (+playdemo auto_record_match, netcon {port})...")
        try:
            self.cs2_proc = subprocess.Popen(cs2_cmd)
        except Exception as e:
            self.log(f"Failed to launch CS2: {e}")
            return

        # Connect Netcon loopback
        time.sleep(2.0)
        self.netcon.try_connect()
        self.log("CS2 launched successfully. Netcon loopback initialized.")

    def stop_cs2(self):
        if self.cs2_proc:
            try:
                self.cs2_proc.terminate()
                self.log("CS2 process terminated.")
            except Exception:
                pass
            self.cs2_proc = None
        self.netcon.disconnect()

    # =========================================================================
    # UPDATES & DESKTOP SHORTCUT
    # =========================================================================
    def _load_local_version(self) -> Dict[str, Any]:
        v_file = os.path.join(self.app_dir, "version.json")
        if os.path.exists(v_file):
            try:
                with open(v_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"commit_sha": "c5d4f11", "version": "1.7.0"}

    @staticmethod
    def _get_desktop_path() -> str:
        if sys.platform == "win32":
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders")
                val, _ = winreg.QueryValueEx(key, "Desktop")
                expanded = os.path.expandvars(val)
                if os.path.exists(expanded):
                    return expanded
            except Exception:
                pass
        return os.path.expanduser(r"~\Desktop")

    def create_desktop_shortcut(self):
        desktop = self._get_desktop_path()
        app_dir = self.app_dir
        pyw_entry = os.path.join(app_dir, "launcher.pyw")
        py_entry = os.path.join(app_dir, "launcher.py")

        python_exe = sys.executable
        pythonw_exe = os.path.join(os.path.dirname(python_exe), "pythonw.exe")
        target_exe = pythonw_exe if os.path.exists(pythonw_exe) else python_exe
        target_script = pyw_entry if os.path.exists(pyw_entry) else py_entry

        shortcut_path = os.path.join(desktop, "CS2 Replay Navigator.lnk")

        vbs_script = f'''
Set oWS = WScript.CreateObject("WScript.Shell")
sLinkFile = "{shortcut_path}"
Set oLink = oWS.CreateShortcut(sLinkFile)
oLink.TargetPath = "{target_exe}"
oLink.Arguments = """{target_script}"""
oLink.WorkingDirectory = "{app_dir}"
oLink.Description = "Counter-Strike 2 Replay & Combat Anomaly Navigator"
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
            messagebox.showinfo("Shortcut Created", f"Successfully created Desktop Shortcut!\n\nLocation:\n{shortcut_path}\n\nYou can now launch CS2 Replay Navigator directly without .bat files.")
        except Exception as e:
            self.log(f"Failed to create desktop shortcut: {e}")
            messagebox.showerror("Shortcut Error", f"Failed to create desktop shortcut:\n{e}")

    def check_and_install_updates(self, silent_if_latest: bool = False):
        def _worker():
            self.log("Connecting to GitHub to verify version...")
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

                local_info = self._load_local_version()
                local_sha = local_info.get("commit_sha", "").strip()

                if local_sha and (remote_sha.startswith(local_sha) or local_sha.startswith(remote_sha_short)):
                    self.log(f"CS2 Replay Navigator is already up to date ({remote_sha_short}: '{commit_msg}').")
                    if not silent_if_latest:
                        messagebox.showinfo("Already Up to Date", f"CS2 Replay Navigator is already up to date!\n\nVersion: {remote_sha_short}\nLatest: {commit_msg}")
                    return

                self.log(f"New update available: {local_sha[:7] or 'Unknown'} -> {remote_sha_short} ('{commit_msg}')")
                if not messagebox.askyesno("Update Available", f"A new update is available!\n\nVersion: {remote_sha_short}\nNotes: {commit_msg}\n\nDownload and install now?"):
                    return

                req_zip = urllib.request.Request(zip_url, headers=headers)
                with urllib.request.urlopen(req_zip, timeout=20) as resp:
                    zip_data = resp.read()

                app_dir = self.app_dir
                updated_count = 0
                with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
                    for name in zf.namelist():
                        parts = name.split("/", 1)
                        if len(parts) < 2 or not parts[1]:
                            continue
                        rel_file = parts[1]
                        if rel_file.endswith((".py", ".pyw", ".bat", ".md", ".txt", ".cfg", ".json")):
                            dest_path = os.path.join(app_dir, rel_file)
                            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                            with open(dest_path, "wb") as f_out:
                                f_out.write(zf.read(name))
                            updated_count += 1

                new_version = {
                    "version": "1.7.0",
                    "commit_sha": remote_sha_short,
                    "commit_msg": commit_msg,
                    "updated_at": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                v_file = os.path.join(app_dir, "version.json")
                with open(v_file, "w", encoding="utf-8") as f:
                    json.dump(new_version, f, indent=2)

                self.log(f"Updated {updated_count} files to {remote_sha_short}. Restarting...")
                self._restart_launcher()
            except Exception as e:
                self.log(f"Update failed: {e}")
                if not silent_if_latest:
                    messagebox.showerror("Update Error", f"Failed to check updates:\n{e}")

        threading.Thread(target=_worker, daemon=True).start()

    def _restart_launcher(self):
        app_dir = self.app_dir
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
        except Exception:
            pass

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = ReplayStudioApp()
    app.run()
