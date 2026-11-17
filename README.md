# Counter-Strike 2 Replay Studio

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?logo=python&logoColor=white)](https://python.org)
[![Platform](https://img.shields.io/badge/Platform-Windows%20x64-0078D6?logo=windows&logoColor=white)](https://microsoft.com)
[![Protocol](https://img.shields.io/badge/Wire-PBDEMS2%20(64.0%20Hz)-6366F1)](https://github.com/Hanzkii/cs2-replay-studio)
[![Engine](https://img.shields.io/badge/Engine-Source%202%20Netcon-FF4500)](https://developer.valvesoftware.com)
[![Dependencies](https://img.shields.io/badge/Dependencies-demoparser2-10B981)](#system-requirements)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

An intuitive, dark-themed native desktop replay studio, combat investigator, and match companion for **Counter-Strike 2** match recordings (`.dem`).

Powered by high-precision Source 2 demo parsing (`demoparser2`), 3D spatial raycast crosshair alignment algorithms, aimbot headshot snap verification, and **1-click Netcon engine synchronization** that instantly seeks CS2 to the exact moment in 1st person with configurable lead-up and slow motion.

---

## Core Capabilities

### 1. 3D Spatial Raycast & Combat Anomaly Engine
- **Mathematical Aim Snap Detection**: Evaluates the shooter's exact eye position $\vec{P}_{\text{shooter}} = (x_s, y_s, z_s + 64.0\text{ u})$ and view direction vector $\vec{v} = (\cos(p)\cos(y), \cos(p)\sin(y), -\sin(p))$ against the victim's 3D hitbox centroid $\vec{P}_{\text{victim}}$.
- **Angular Crosshair Error Calculation**: Computes the exact angular offset $\theta_{\text{offset}} = \arccos(\vec{v} \cdot \vec{d})$ and perpendicular ray-to-target distance $\Delta r = \|\vec{\Delta} \times \vec{v}\|$.
- **Eliminates False Positives**:
  - **Aimbot Snaps (`CRITICAL`)**: Crosshair locked onto the head bone ($\theta_{\text{offset}} \le 0.85^\circ$, $\Delta r < 15.0\text{ u}$).
  - **Suspicious Hits (`SUSPICIOUS`)**: Tight angular raycast alignments ($\theta_{\text{offset}} < 1.50^\circ$).
  - **Combat Frags (`INFO`)**: Filterable spray transfers, body hits, and standard weapon eliminations.

### 2. 1-Click Netcon Engine Synchronization (`-netconport 2121`)
- **Direct Engine Seeking**: Clicking any event row in the table automatically:
  - Seeks CS2 demo playback to **1.5 seconds before the action** (`lead_tick = tick - 96`).
  - Sets **First-Person Spectator Mode** (`spec_mode 1`).
  - Locks the camera onto the shooter (`spec_player "<suspect>"`).
  - Slows playback down to **$0.25\times$ speed** (`demo_timescale 0.25`) with background reinforcement to prevent camera reset.
- **Integrated Transport Controller**: Play/pause toggling (`demo_togglepause`), seek $\pm 64$ ticks, step rounds, speed presets ($0.25\times, 0.5\times, 1.0\times, 2.0\times$), and 1st-person camera lock.
- **In-Engine Debug Overlays**: Toggle lag compensation bounding boxes (`sv_showlagcompensation 1`) and bullet impacts (`sv_showimpacts 1`) directly from the studio.

### 3. Interactive Visual Scrubber & Filtering
- **Full-Match Timeline Scrubber**: Displays round markers, kill pips, and anomaly pins across the match length ($0 \dots N$ ticks). Click anywhere to seek in real-time.
- **Multi-Vector Filtering**: Filter events by Suspect/Player, Category (`AIMBOT_SNAP`, `SUSPICIOUS_HIT`, `COMBAT_KILL`), Severity (`CRITICAL`, `SUSPICIOUS`, `INFO`), or search query.

---

## Development Roadmap: Unified Match Companion

The project is evolving from a pure anti-cheat auditor into a comprehensive **Match Companion** covering three core domains:

```
                               ┌────────────────────────────────────────────────────────┐
                               │                 CS2 Replay Studio                      │
                               └──────────────────────────┬─────────────────────────────┘
                                                          │
                    ┌─────────────────────────────────────┼────────────────────────────────────┐
                    ▼                                     ▼                                    ▼
       ┌────────────────────────┐            ┌────────────────────────┐           ┌────────────────────────┐
       │  🛡️ Mode 1: Audit      │            │  🌟 Mode 2: Highlights │           │  🎯 Mode 3: Duels      │
       │  Anti-Cheat & Suspect  │            │  Frag Reel & Clutches  │           │  Coaching & Entry Frag │
       └────────────┬───────────┘            └────────────┬───────────┘           └────────────┬───────────┘
                    │                                     │                                    │
                    ▼                                     ▼                                    ▼
       • 3D Raycast Aimbot Snaps             • Aces (5K) & Multi-Kills (3K/4K)    • Opening Duels (First K/D)
       • Wallhack/ESP Pre-Aim Tracking       • Sniper Noscopes & Air Shots        • Trade Frag Efficiency (< 3s)
       • Inhuman Reaction Triggers (<80ms)   • 1vX Clutch Round Wins              • Crosshair Placement Rating
       • Through-Smoke Radar Verifications   • Collaterals & Wallbang Highlights  • First-Bullet Accuracy Stats
```

See [ROADMAP.md](ROADMAP.md) for the detailed phase breakdown and feature specifications.

---

## Quickstart

### 1. Installation
Clone the repository and install dependencies:
```bash
git clone https://github.com/Hanzkii/cs2-replay-studio.git
cd cs2-replay-studio
pip install -r requirements.txt
```

### 2. Launching the Studio
Double-click **`LAUNCH_CONTROL_CENTER.bat`** (or `launcher.pyw`):
1. Click **`📁 Browse .dem File...`** to load any CS2 match replay (`.dem`).
2. Click **`▶ LAUNCH CS2 & SYNC`** to start Counter-Strike 2 in Borderless Windowed mode with Netcon enabled.
3. Browse the **Combat & Anomaly Table**, click any event row, and CS2 will automatically jump to 1.5s before the shot in slow motion.

### 3. Desktop Shortcut
Click **`📌 Desktop Icon`** inside the studio header to generate a native Windows desktop shortcut (`CS2 Replay Studio.lnk`) for 1-click launching.

---

## Project Architecture

```
cs2-replay-studio/
├── launcher.py               # Desktop GUI Replay Studio & Anomaly Navigator (Tkinter)
├── launcher.pyw              # Windowless direct launch entrypoint
├── demo_parser.py            # 3D spatial raycast math & Source 2 demoparser2 event engine
├── engine_link.py            # Steam/CS2 auto-discovery & Netcon TCP socket client
├── LAUNCH_CONTROL_CENTER.bat # 1-click desktop batch launcher
├── DRAG_AND_DROP_DEMO_HERE.bat # Drag-and-drop batch runner
├── ROADMAP.md                # Development roadmap for match companion phases
├── requirements.txt          # Python dependencies (demoparser2, polars, pyarrow)
├── version.json              # Version metadata and update tracking
└── README.md                 # Complete documentation & usage guide
```

---

## System Requirements

- **Operating System**: Windows 10 or Windows 11 (64-bit)
- **Python**: Python 3.8 or newer (Standard installation or WindowsApps with Tkinter enabled)
- **Game**: Counter-Strike 2 installed via Steam
- **Dependencies**: `demoparser2`, `polars`, `pyarrow`, `pandas` (see `requirements.txt`)

---

## Security & Fair Play Standards

- **Static Replay Analysis Only**: All analysis is performed offline directly on recorded demo files (`.dem`).
- **Standard Netcon TCP Protocol**: In-engine seeking communicates strictly via Valve's documented developer console loopback interface (`-netconport`). Zero DLL injection, dynamic memory reading/writing, or live process tampering.
