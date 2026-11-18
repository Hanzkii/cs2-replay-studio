# CS2 Replay Studio: Development Roadmap

> **Vision**: Transform CS2 Replay Studio into a unified **Match Companion** that combines rapid **Suspect Anti-Cheat Auditing**, **Match Highlights Navigation**, and **Performance/Duel Coaching** into an instant 1-click spectator experience.

---

## Architecture Overview

```
                               ┌────────────────────────────────────────────────────────┐
                               │           CS2 Replay Studio & Navigator                │
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

---

## Phase 1: 🛡️ Suspect & Anti-Cheat Audit (Enhanced)

*Building on the verified 3D spatial raycasting engine to detect common third-party assistance vectors:*

- [x] **3D Spatial Raycast Aimbot Verification**:
  - Exact shooter eye origin $\vec{P}_{\text{eye}} = (x_s, y_s, z_s + 64.0\text{ u})$.
  - Victim target origin $\vec{P}_{\text{target}} = (x_v, y_v, z_v + 62.0\text{ u})$ (Head bone centroid).
  - Forward view vector $\vec{v} = (\cos(p)\cos(y), \cos(p)\sin(y), -\sin(p))$.
  - Angular alignment error $\theta_{\text{offset}} = \arccos(\vec{v} \cdot \vec{d})$.
  - True snap detection threshold: $\theta_{\text{offset}} < 0.85^\circ$ with perpendicular ray distance $\Delta r < 15.0\text{ u}$.
- [ ] **Match Integrity & Outlier Threat Assessment Banner**:
  - Automatically evaluate anomaly concentration across all match players upon demo ingestion.
  - **Single Suspect Outlier Detection**: Statistically flag when an isolated player accounts for the vast majority of critical aimbot snaps (e.g. $\ge 60\%$ concentration or $\ge 3\times$ the runner-up) while other players exhibit standard human distributions.
  - **Dynamic Banner Readout**: Prominent status indicator above the table (`🚨 PRIME SUSPECT OUTLIER: [Player] (X Snaps)` vs `✅ INTEGRITY NOMINAL: Normal match spread`).
  - **1-Click Suspect Isolation**: One-click action button (`[ 🎯 Audit Suspect ]`) that instantly filters the timeline and event table directly to that player's engagements.
  - **Dropdown Threat Badging**: Annotate the suspect dropdown with per-player snap counts (e.g. `PlayerName (X snaps)`).
- [ ] **Wallhack / ESP Crosshair Tracking**:
  - Detect continuous angular tracking of enemy origin vectors behind opaque brush/model geometry before line-of-sight is established.
  - Flag suspicious pre-aim locking prior to corner emergence.
- [ ] **Triggerbot & Reaction Latency Audit**:
  - Calculate discrete delta ticks between when an enemy hitbox first crosses the player's view frustum and when weapon discharge (`+attack`) occurs.
  - Flag reaction times $< 80\text{ ms}$ (well below human cognitive reaction limits).
- [ ] **Through-Smoke & Flashbang Radar Audit**:
  - Filter and inspect kills where `thrusmoke == True` or `attackerblind == True`.
  - Automatic 1-click spectator inspection to visually review whether the suspect tracked player models through smoke sprites.
- [ ] **Shareable Suspect Dossier**:
  - Generate a concise Markdown / JSON summary of a suspect player's suspicious engagements with exact ticks, round numbers, and mathematical confidence metrics.

---

## Phase 2: 🌟 Match Highlights & Frag Reel Navigator

*Providing instant 1-click jumps to the most exciting rounds and moments for players and content creators:*

- [ ] **Multi-Kill Round Clusters**:
  - **Aces (5K)**: Identify all rounds where a single player scores 5 eliminations.
  - **Quad-Kills (4K) & Triple-Kills (3K)**: Rapid multi-frag events grouped by round.
- [ ] **Specialist Weapon Feats**:
  - **Noscopes**: Long-range sniper kills without scoping (`noscope == True`).
  - **Jump Shots / Mid-Air Kills**: Eliminations landed while in mid-air (`attackerinair == True`).
  - **Wallbang Highlights**: Kills scored through multiple penetrable surfaces (`penetrated > 0`).
- [ ] **Clutch Situation Tracker**:
  - Identify 1v1, 1v2, 1v3, 1v4, and 1v5 clutch rounds based on team alive state before round resolution (`round_end`).
  - Jump directly to the moment the clutch scenario begins.
- [ ] **Highlight Reel Auto-Play**:
  - Sequential playback mode: automatically jump through all highlights for a selected player with automated pre-roll and post-kill transition timers.

---

## Phase 3: 🎯 Duels & Performance Coaching

*Actionable data for personal self-improvement, team reviews, and tactical analysis:*

- [ ] **Opening Duels (Entry Fragging)**:
  - Isolate the first kill and first death of every single round.
  - Calculate Opening Duel Win Rate % per player, CT vs T side.
- [ ] **Trade Fragging Efficiency**:
  - Detect whether a player's death was traded by a teammate within a 3.0-second window.
  - Flag untraded deaths and isolate instances where trade spacing was inadequate.
- [ ] **Crosshair Placement Angle Metric**:
  - Measure the angular distance between the player's crosshair and the enemy's head when the enemy first appears on screen.
  - Lower initial angular delta = superior pre-aim and crosshair placement discipline.
- [ ] **Time-to-Damage (TTD)**:
  - Measure elapsed time from initial visual contact to the first landed hitgroup damage impact.

---

## User Interface & Experience Design

### Mode Filter Switcher
The top of the main table will feature four dedicated view pills:
```
[ All Events ]  [ 🛡️ Suspect Audit ]  [ 🌟 Match Highlights ]  [ 🎯 Duels & Coaching ]
```

### 1-Click Engine Action
All three modes share the unified Netcon synchronization pipeline:
1. **Pre-Roll Jump**: Jumps $1.5\text{ s}$ (96 ticks) before the key moment so setup, positioning, and movement are visible.
2. **First-Person Lock**: Forces `spec_mode 1` and `spec_player "<player>"`.
3. **Adaptive Timescale**:
   - For **Suspect Audit**: Defaults to $0.25\times$ super slow-motion to analyze crosshair micro-adjustments.
   - For **Highlights & Duels**: Defaults to $1.0\times$ full-speed (with user option for $0.5\times$).
4. **Director Reinforcement**: Re-sends camera locks after tick seek settles to prevent engine camera reset.

---

## Technical Dependencies & Compatibility

- **Parsing Engine**: `demoparser2` (C++ / Rust bindings for Source 2 protobufs) for microsecond event extraction, with pure-Python fallback diagnostics.
- **Engine Protocol**: Valve Source 2 TCP Netcon interface (`-netconport 2121`).
- **Target OS**: Windows 10/11 x64.
- **Python Compatibility**: Python 3.8 through 3.14+ (fully verified across standard CPython and WindowsApps environments).
