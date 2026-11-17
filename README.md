# Counter-Strike 2 Sub-Tick Replay Studio & In-Game HUD Overlay

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?logo=python&logoColor=white)](https://python.org)
[![Platform](https://img.shields.io/badge/Platform-Windows%20x64-0078D6?logo=windows&logoColor=white)](https://microsoft.com)
[![Protocol](https://img.shields.io/badge/Wire-PBDEMS2%20(64.0%20Hz)-6366F1)](https://github.com/Hanzkii/cs2-replay-overlay)
[![Dependencies](https://img.shields.io/badge/Dependencies-Zero%20pip%20installs-10B981)](#installation)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

An intuitive, dark-themed native desktop control center and transparent in-game HUD overlay for **Counter-Strike 2** match recordings (`.dem`).

Visualizes server-authoritative sub-tick timing micro-slicing ($15.625\text{ ms}$ discrete window), 3D rewound lag compensation hitboxes (`Apex Joint #6`), bullet ray-trace vectors, and desync anomalies directly on top of CS2 during demo viewing in real time.

---

## Key Capabilities

- **Zero Pip Dependencies**: Runs entirely on pure Python 3 standard library (`tkinter`, `ctypes`, `socket`, `struct`). No complex build chains or virtual environment setups required.
- **Non-Invasive & Anticheat Safe**: Employs an external Win32 transparent click-through layered HUD window (`WS_EX_LAYERED | WS_EX_TRANSPARENT`). Zero DLL injection and zero live process memory modification (runs cleanly with CS2 `-insecure`).
- **Automated Steam & CS2 Discovery**: Automatically scans the Windows Registry and parses `libraryfolders.vdf` across all local drives to locate `cs2.exe` and `game/csgo/` without manual configuration.
- **Pure Python PBDEMS2 Parser**: Reads protobuf container headers and Google Snappy compression frames directly in Python to inspect map names, build numbers, tickrates, and match metrics.
- **Real-Time Engine Sync**: Uses CS2's local loopback console socket (`-netconport 2121`) to send transport commands (`demo_pause`, `demo_resume`, `demo_gototick`) and synchronize ticks.

---

## In-Game Visual Layers

| Layer | Visual Component | Description |
| :--- | :--- | :--- |
| **Layer 1** | **Sub-Tick Micro-Slice Bar** | Top HUD displaying the $15.625\text{ ms}$ discrete tick window with exact fractional actuation timestamp $w \in [0.0, 1.0)$ ($t = w \times 15.625\text{ ms}$), input button state (`+attack`), and monotonicity audit status. |
| **Layer 2** | **3D Rewound Lag Comp Hitbox** | Projects server-authoritative rewound player positions at $t - \Delta t_{\text{unlag}}$ directly around player models using Source 2 $4 \times 4$ ViewMatrix math. Renders wireframe capsule and `Apex Joint #6` head bone sphere (Neon Emerald for hit, Vivid Ruby for desync miss). |
| **Layer 3** | **Bullet Ray-Trace & Trajectory Vector** | Directional vector traced from the shooter eye position through the crosshair to the hit target with exact perpendicular distance callout ($\Delta r \le 4.0\text{ u}$ hit confirmation). |
| **Layer 4** | **Desync & Anomaly HUD Alerts** | Real-time diagnostic cards in the bottom corner alerting to teleport threshold breaches ($> 64.0\text{ u}$), $sv\_maxunlag$ rollback window clamps ($200.0\text{ ms}$ limit), and packet dropouts. |
| **Layer 5** | **In-Game Settings Menu HUD** | Interactive dark translucent panel toggleable via hotkey (`F1` or `INSERT`). When open, unlocks mouse clicks to toggle individual layers, scrub the demo timeline, and control playback speed. |

---

## In-Game Hotkey Reference

| Hotkey | Action |
| :--- | :--- |
| **`F1`** or **`INSERT`** | **Toggle Settings Menu** (unlocks mouse cursor to click toggles & timeline scrubber) |
| **`SPACE`** | **Pause / Resume** CS2 demo playback (sent via Netcon port 2121) |
| **`←` / `→`** | **Seek $\pm 64$ Ticks** ($\pm 1.0$ second scrub) |
| **`F2`** | Quick Toggle: **3D Rewound Hitboxes** |
| **`F3`** | Quick Toggle: **Sub-Tick Micro-Slice Bar** |
| **`F4`** | Quick Toggle: **Bullet Ray-Trace Vectors** |
| **`F5`** | Quick Toggle: **Anomaly & Desync Alerts** |
| **`F11`** or **`F10`** | **Emergency Master Toggle**: Instantly hide / reveal overlay |
| **`ESC`** | Close Settings Menu & lock mouse back to game |

---

## Quickstart

### Method 1: Desktop GUI Control Center (Recommended)
Double-click **`LAUNCH_CONTROL_CENTER.bat`** (or run `python launcher.py`).
1. Click **`📁 Browse .dem File...`** to pick any match replay.
2. Toggle desired overlay layers.
3. Click **`▶ LAUNCH REPLAY WITH OVERLAYS`**.

### Method 2: Instant Drag-and-Drop
Drag and drop any `.dem` match recording file directly onto **`DRAG_AND_DROP_DEMO_HERE.bat`**.
The launcher will parse demo headers, stage the match demo, start CS2 in Borderless Windowed mode, and snap the transparent HUD overlay automatically.

### Method 3: Command Line
```powershell
# Open control center with a specific demo loaded
python launcher.py "C:\path\to\match.dem"

# Launch in-game overlay directly (if CS2 is already running)
python overlay.py "C:\path\to\match.dem" --netcon-port 2121
```

---

## Project Architecture

```
cs2-replay-overlay/
├── launcher.py               # Desktop GUI Control Center (Tkinter)
├── overlay.py                # Win32 transparent click-through HUD overlay
├── demo_parser.py            # Pure Python PBDEMS2 container & Snappy decompressor
├── engine_link.py            # Steam/CS2 auto-discovery & Netcon TCP console client
├── camera.py                 # Source 2 4x4 ViewMatrix & WorldToScreen projection
├── LAUNCH_CONTROL_CENTER.bat # 1-click launcher for the desktop GUI
├── DRAG_AND_DROP_DEMO_HERE.bat # 1-click drag & drop batch runner
├── requirements.txt          # Zero pip dependencies documentation
└── README.md                 # Complete documentation & usage guide
```

---

## System Requirements

- **Operating System**: Windows 10 or Windows 11 (64-bit)
- **Python**: Python 3.8 or newer (Standard installation with Tkinter enabled)
- **Game**: Counter-Strike 2 installed via Steam
- **Display Mode**: Borderless Windowed (`-windowed -noborder`, applied automatically by launcher)

---

## License

MIT License. Open-source replay analysis and research software.
