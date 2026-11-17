# Counter-Strike 2 Sub-Tick Replay Studio // Native Panorama UI

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?logo=python&logoColor=white)](https://python.org)
[![Platform](https://img.shields.io/badge/Platform-Windows%20x64-0078D6?logo=windows&logoColor=white)](https://microsoft.com)
[![Protocol](https://img.shields.io/badge/Wire-PBDEMS2%20(64.0%20Hz)-6366F1)](https://github.com/Hanzkii/cs2-replay-overlay)
[![Engine](https://img.shields.io/badge/Engine-Source%202%20Panorama-FF4500)](https://developer.valvesoftware.com/wiki/CSGO_Panorama_API)
[![Dependencies](https://img.shields.io/badge/Dependencies-Zero%20pip%20installs-10B981)](#system-requirements)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

An intuitive, dark-themed native desktop control center and **100% native in-engine Source 2 Panorama UI suite** for **Counter-Strike 2** match recordings (`.dem`).

Visualizes server-authoritative sub-tick timing micro-slicing ($15.625\text{ ms}$ discrete window), 3D rewound lag compensation hitboxes (`Apex Joint #6`), bullet ray-trace vectors, and desync anomalies natively inside CS2 using Valve's Panorama UI engine with authentic 1:1 game visuals.

---

## Why Native Panorama UI?

1. **Zero External Window Clutter**: Runs directly inside `cs2.exe` via DirectX 11 / Vulkan GPU pipeline. No floating transparent desktop windows.
2. **Zero Mouse Capture or Camera Lock**: Freecam roaming, Chase Cam, and First-Person mouse look work natively with zero input hindrance.
3. **Automatic Game Lifecycle Sync**: Closes automatically with Counter-Strike 2; never stays active or lingering on the desktop.
4. **Authentic CS2 Design System**: Utilizes native `Stratum2` fonts, dark glass blur backdrops (`#090d1bf2`), neon cyan (`#38bdf8`) / emerald (`#34d399`) / coral (`#f43f5e`) accents, and responsive flexbox layouts.

---

## In-Engine Visual Layers

| Layer | Visual Component | Description |
| :--- | :--- | :--- |
| **Layer 1** | **Sub-Tick Micro-Slice Bar** | Top HUD docked below scoreboard showing the $15.625\text{ ms}$ tick window with exact fractional actuation timestamp $w \in [0.0, 1.0)$ ($t = w \times 15.625\text{ ms}$), weapon state (`+attack`), and monotonicity audit. |
| **Layer 2** | **3D Rewound Hitbox Spatial Reticle** | Displays server-authoritative rewound player positions at $t - \Delta t_{\text{unlag}}$ with `Apex Joint #6` head bone indicator (Emerald for hit, Coral for desync miss). |
| **Layer 3** | **Bullet Ray-Trace & Trajectory Vector** | Vector traced from shooter eye position to impact target with exact distance callout ($\Delta r \le 4.0\text{ u}$ hit confirmation). |
| **Layer 4** | **Desync & Anomaly HUD Alerts** | Real-time diagnostic cards docked on the right alerting to $sv\_maxunlag$ rollback window clamps ($200.0\text{ ms}$ limit) and desync discrepancies. |
| **Layer 5** | **In-Engine Settings & Anomaly Navigator Modal** | Interactive dark translucent panel toggleable via **`[F1]`**. Allows layer toggling, camera perspective cycling, live diagnostics, and 1-click anomaly jumping (`▶ GO`). |

---

## In-Game Hotkey Reference

| Hotkey | Action |
| :--- | :--- |
| **`[F1]`** | **Toggle Settings & Anomaly Navigator Modal** (unlocks mouse cursor to click toggles & timeline scrubber) |
| **`[SPACE]`** | **Pause / Resume** CS2 demo playback (`demo_togglepause`) |
| **`[←] / [→]`** | **Seek $\pm 64$ Ticks** ($\pm 1.0$ second scrub) |
| **`[F6]`** | **Trigger Sub-Tick Test Shot & Parity Audit** |
| **`[F7]`** | **Toggle Live Always-On HUD vs Event-Only** |
| **`[F8]`** | **Cycle Cam Perspective** (First-Person `spec_mode 4`, Chase Cam `spec_mode 5`, Freecam `spec_mode 1`) |
| **`[ESC]`** | Close in-engine modal and return focus to game |

---

## Quickstart

### Method 1: Desktop GUI Control Center (Recommended)
Double-click **`LAUNCH_CONTROL_CENTER.bat`** (or `launcher.pyw`):
1. Click **`📁 Browse .dem File...`** to pick any match replay.
2. Click **`▶ LAUNCH REPLAY (NATIVE PANORAMA HUD)`**.
3. CS2 launches with native Panorama HUD automatically deployed and loaded. Press **`[F1]`** in-game to toggle settings.

### Method 2: Instant Drag-and-Drop
Drag and drop any `.dem` match recording file directly onto **`DRAG_AND_DROP_DEMO_HERE.bat`**.
The launcher will parse demo headers, stage the match demo, deploy Panorama assets to `game/csgo/panorama/`, and start CS2 in Borderless Windowed mode.

---

## Project Architecture

```
cs2-replay-overlay/
├── launcher.py               # Desktop GUI Control Center (Tkinter)
├── launcher.pyw              # Windowless direct launch entrypoint
├── demo_parser.py            # Pure Python PBDEMS2 container & Snappy decompressor
├── engine_link.py            # Steam/CS2 auto-discovery & Netcon TCP console client
├── panorama/                 # Native In-Engine CS2 Panorama UI Suite
│   ├── layout/
│   │   ├── subtick_hud.xml   # Core Sub-Tick HUD, Anomaly Cards & Settings Modal
│   │   ├── demo_viewer.xml   # In-engine demo player integration mount
│   │   └── spec_hud.xml      # Spectator HUD mount
│   ├── styles/
│   │   └── subtick_hud.css   # Authentic CS2 dark glass CSS3 flexbox styling
│   └── scripts/
│       └── subtick_hud.js    # 60 FPS DemoAPI sync, GameEvents & transport logic
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
