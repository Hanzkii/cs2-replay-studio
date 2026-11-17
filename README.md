# Counter-Strike 2 Sub-Tick Replay & Anomaly Studio

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?logo=python&logoColor=white)](https://python.org)
[![Platform](https://img.shields.io/badge/Platform-Windows%20x64-0078D6?logo=windows&logoColor=white)](https://microsoft.com)
[![Protocol](https://img.shields.io/badge/Wire-PBDEMS2%20(64.0%20Hz)-6366F1)](https://github.com/Hanzkii/cs2-replay-overlay)
[![Engine](https://img.shields.io/badge/Engine-Source%202%20Netcon-FF4500)](https://developer.valvesoftware.com)
[![Dependencies](https://img.shields.io/badge/Dependencies-Zero%20pip%20installs-10B981)](#system-requirements)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

An intuitive, dark-themed native desktop replay studio, combat investigator, and automated anti-cheat diagnostic station for **Counter-Strike 2** match recordings (`.dem`).

Features automated full-match bitstream parsing, sub-tick micro-slice timing audits, aimbot viewangle snap velocity analysis ($\Delta \theta > 35^\circ/\text{tick}$), triggerbot clustering detection ($w < 2.0\text{ ms}$), and **1-click Netcon engine synchronization** that instantly seeks CS2 to the exact anomaly moment while spectating the suspect.

---

## Core Capabilities

### 1. Automated Anti-Cheat & Anomaly Engine
- **Aimbot Snap Velocity Scanner**: Scans player viewangles between ticks. Automatically detects and flags angular delta spikes ($\Delta \theta > 35^\circ/\text{tick}$) with high instantaneous deceleration characteristic of silent aim and robotic crosshair locking.
- **Sub-Tick Triggerbot Cluster Audit**: Evaluates actuation timing offsets $w \in [0.0, 1.0)$ ($0.0\text{ ms} \dots 15.625\text{ ms}$). Flags inhuman clustering patterns ($\sigma < 0.8\text{ ms}$) and reaction latencies $< 50\text{ ms}$.
- **Lag Compensation Desync & Backtrack Analysis**: Identifies hit registration events where victim interpolation rollback exceeded standard limits ($> 100\text{ ms}$) or bullet raycast distance delta exceeded bounding box margins ($> 4.0\text{ u}$).
- **Rapid Fire Command Injection**: Audits sub-tick packet queues for cyclic weapon cooldown violations.

### 2. 1-Click Netcon Engine Synchronization (`-netconport 2121`)
- **Direct Engine Seeking**: Click `[▶ Jump to Event & Spectate in CS2]` on any flagged anomaly or combat kill. The studio dispatches `demo_gototick <tick - 32>` (half-second pre-roll) and locks camera focus via `spec_player "<suspect>"`.
- **Integrated Transport Controller**: Full play/pause toggling (`demo_togglepause`), seek $\pm 64$ ticks, step rounds, and speed presets ($0.25\times, 0.5\times, 1.0\times, 2.0\times$).
- **Anti-Cheat Debug Overlays**: Toggle in-engine lag compensation hitboxes (`sv_showlagcompensation 1`), bullet impacts (`sv_showimpacts 1`), and wireframe models (`r_drawothermodels 2`) directly from the studio.

### 3. Interactive Visual Scrubber & Telemetry Graphing
- **Full-Match Timeline Scrubber**: Displays round markers, kill pips, damage hits, and flagged anomaly pins across the match length ($0 \dots N$ ticks). Click or drag anywhere to seek in real-time.
- **Sub-Tick Micro-Slice Visualizer**: Graphs attack actuation timestamps across the $15.625\text{ ms}$ discrete tick window, separating normal Gaussian human click distributions from machine triggerbot clusters.
- **Angular Velocity Spike Plot**: Plots viewangle angular velocity ($\Delta \theta/\text{tick}$) over time for any selected player.

---

## Quickstart

### Method 1: Desktop Control Center (Recommended)
Double-click **`LAUNCH_CONTROL_CENTER.bat`** (or `launcher.pyw`):
1. Click **`📁 Browse .dem File...`** to pick any match replay (or drag and drop `.dem`).
2. The studio automatically parses match metadata, player rosters, and flags all anomalies in $< 1.0$ second.
3. Click **`▶ LAUNCH CS2 & SYNC`** to start Counter-Strike 2 in Borderless Windowed mode with Netcon enabled.
4. Browse the **Anomaly Table**, select any suspicious action, and click **`▶ JUMP TO EVENT`** to inspect the play in CS2.

### Method 2: Instant Desktop Shortcut
Click **`📌 Desktop Icon`** inside the studio header to generate a native Windows desktop shortcut (`CS2 Replay Studio.lnk`) pointing directly to `pythonw launcher.pyw` for 1-click launching without batch consoles.

---

## Project Architecture

```
cs2-replay-overlay/
├── launcher.py               # Desktop GUI Replay Studio & Anomaly Inspector (Tkinter)
├── launcher.pyw              # Windowless direct launch entrypoint
├── demo_parser.py            # Pure Python PBDEMS2 container, Snappy codec & Anomaly Engine
├── engine_link.py            # Steam/CS2 auto-discovery & Netcon TCP console client
├── LAUNCH_CONTROL_CENTER.bat # 1-click launcher for the desktop GUI
├── DRAG_AND_DROP_DEMO_HERE.bat # 1-click drag & drop batch runner
├── version.json              # Version metadata and update tracking
├── requirements.txt          # Zero pip dependencies documentation
└── README.md                 # Complete documentation & usage guide
```

---

## System Requirements

- **Operating System**: Windows 10 or Windows 11 (64-bit)
- **Python**: Python 3.8 or newer (Standard installation with Tkinter enabled)
- **Game**: Counter-Strike 2 installed via Steam
- **Dependencies**: **Zero third-party pip dependencies** (Pure Python standard library)
