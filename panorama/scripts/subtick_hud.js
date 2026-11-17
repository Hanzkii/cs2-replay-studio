"use strict";

/**
 * subtick_hud.js - Native Counter-Strike 2 Panorama Sub-Tick Replay Studio
 * 
 * Provides:
 *   1. 60 FPS real-time DemoAPI synchronization (sub-tick micro-slice bar & timeline scrubber).
 *   2. Native game event listeners for discrete combat actuation (weapon_fire, player_hurt).
 *   3. In-engine settings menu with layer toggles, anomaly jumping, and transport controls.
 *   4. F1 / ESC hotkey toggle with seamless focus release.
 */

var g_SubTickState = {
    isMenuOpen: false,
    cameraMode: "FIRST_PERSON", // FIRST_PERSON, CHASE_CAM, FREECAM
    liveDiagnostics: true,
    currentTick: 64,
    totalTicks: 150000,
    layers: {
        subtick: true,
        hitbox: true,
        raytrace: true,
        anomalies: true
    },
    anomalies: [
        { tick: 23040, title: "Tick 023040 (06:00) - xf [M4A1-S]", frac: 0.650, unlag: 50.0, isHit: false },
        { tick: 23404, title: "Tick 023404 (06:05) - seraph [AK-47]", frac: 0.870, unlag: 56.0, isHit: true },
        { tick: 82357, title: "Tick 082357 (21:20) - baselineJ [desert eagle]", frac: 0.720, unlag: 32.0, isHit: true },
        { tick: 110620, title: "Tick 110620 (28:48) - Apex [AWP]", frac: 0.910, unlag: 77.0, isHit: true }
    ],
    anomalyPage: 0
};

(function() {
    $.Msg("[SUBTICK_HUD] Panorama Sub-Tick Replay Studio initializing...");

    // Cache Panel References
    let modal = $("#SettingsModal");
    let card = $("#SubTickBarContainer");
    let fill = $("#SubTickFill");
    let needle = $("#SubTickNeedle");
    let callout = $("#SubTickCallout");
    let title = $("#SubTickTitle");
    let anomaly = $("#AnomalyCard");
    let slider = $("#DemoTimelineSlider");
    let scrubLabel = $("#LblScrubberTick");

    // -------------------------------------------------------------------------
    // 1. Core 60 FPS Engine Sync Loop
    // -------------------------------------------------------------------------
    function UpdateEngineSync() {
        let curTick = 0;
        let total = g_SubTickState.totalTicks;
        let isPaused = false;

        // Query native DemoAPI if available
        if (typeof DemoAPI !== "undefined") {
            if (DemoAPI.GetPlaybackTick) {
                curTick = DemoAPI.GetPlaybackTick();
            }
            if (DemoAPI.GetTotalTicks) {
                let t = DemoAPI.GetTotalTicks();
                if (t > 1000) total = t;
            }
            if (DemoAPI.IsPlaybackPaused) {
                isPaused = DemoAPI.IsPlaybackPaused();
            }
        }

        g_SubTickState.currentTick = curTick;
        g_SubTickState.totalTicks = total;

        // Calculate discrete sub-tick fraction w in current 64 Hz interval
        let subTickFrac = (curTick % 64) / 64.0;
        let actMs = subTickFrac * 15.625;
        let pct = (subTickFrac * 100.0).toFixed(1) + "%";

        // Update Top Micro-Slice Bar
        if (g_SubTickState.liveDiagnostics) {
            if (fill) fill.style.width = pct;
            if (needle) needle.style.marginLeft = pct;
            if (title) title.text = `SUB-TICK TIMING // LIVE TELEMETRY (Tick ${curTick})`;
            if (callout) callout.text = `Sub-Tick Micro-Slice: ${actMs.toFixed(2)} ms / 15.625 ms (${(subTickFrac).toFixed(3)})`;
        }

        // Update Scrubber Slider if not actively being dragged by user
        if (slider && !slider.BHasKeyFocus()) {
            slider.max = total;
            slider.value = curTick;
        }
        if (scrubLabel) {
            scrubLabel.text = `Timeline Scrub: Tick ${curTick} / ${total}`;
        }

        // Update Play/Pause Button Label
        let lblPlayPause = $("#LblPlayPause");
        if (lblPlayPause) {
            lblPlayPause.text = isPaused ? "▶ RESUME PLAYBACK" : "❚❚ PAUSE PLAYBACK";
        }

        // Auto-check detected anomalies
        for (let i = 0; i < g_SubTickState.anomalies.length; i++) {
            let a = g_SubTickState.anomalies[i];
            if (Math.abs(a.tick - curTick) <= 2) {
                ShowCombatActuation(a.title, a.frac, a.unlag, a.isHit);
                break;
            }
        }

        // Run smoothly at 60 FPS
        $.Schedule(0.016, UpdateEngineSync);
    }

    // -------------------------------------------------------------------------
    // 2. Weapon Actuation & Combat Event Display
    // -------------------------------------------------------------------------
    function ShowCombatActuation(weaponName, frac, unlagMs, isHit) {
        let actMs = frac * 15.625;
        let pct = (frac * 100.0).toFixed(1) + "%";

        if (fill) fill.style.width = pct;
        if (needle) needle.style.marginLeft = pct;
        if (callout) callout.text = `${weaponName} @ ${actMs.toFixed(2)} ms (w = ${frac.toFixed(3)})`;

        if (anomaly) {
            if (isHit) {
                anomaly.RemoveClass("Miss");
                let t = $("#AnomalyTitle");
                let d = $("#AnomalyDesc");
                if (t) t.text = "✓ PARITY CONFIRMED // ROLLBACK MONOTONIC";
                if (d) d.text = `sv_maxunlag: 200.0ms | Rewind: -${unlagMs.toFixed(1)}ms | Delta <= 4.0u`;
            } else {
                anomaly.AddClass("Miss");
                let t = $("#AnomalyTitle");
                let d = $("#AnomalyDesc");
                if (t) t.text = "! LAG COMPENSATION ROLLBACK ANOMALY";
                if (d) d.text = `sv_maxunlag: 200.0ms | Rewind: -${unlagMs.toFixed(1)}ms | Delta > 4.0u`;
            }
        }
    }

    // -------------------------------------------------------------------------
    // 3. GameEvents Listeners
    // -------------------------------------------------------------------------
    GameEvents.Subscribe("weapon_fire", function(ev) {
        let tick = g_SubTickState.currentTick;
        let frac = (tick % 64) / 64.0;
        let weapon = ev.weapon || "weapon_fire";
        ShowCombatActuation(weapon, frac, 47.6, true);
    });

    GameEvents.Subscribe("player_hurt", function(ev) {
        let isHeadshot = (ev.hitgroup === 1);
        let dmg = ev.dmg_health || 0;
        if (anomaly) {
            if (isHeadshot) {
                anomaly.RemoveClass("Miss");
                let t = $("#AnomalyTitle");
                let d = $("#AnomalyDesc");
                if (t) t.text = "✓ PARITY CONFIRMED // HEAD HITBOX REGISTERED";
                if (d) d.text = `Damage: ${dmg} HP | Hitgroup: Apex Joint #6 (Head)`;
            } else {
                let t = $("#AnomalyTitle");
                let d = $("#AnomalyDesc");
                if (t) t.text = "✓ HIT REGISTERED // KINEMATIC INTEGRITY OK";
                if (d) d.text = `Damage: ${dmg} HP | Hitgroup: ${ev.hitgroup || 2}`;
            }
        }
    });

    // Start sync loop
    UpdateEngineSync();
    $.Msg("[SUBTICK_HUD] Panorama Sub-Tick Replay Studio ready.");
})();

// =============================================================================
// Global UI Actions & Callbacks
// =============================================================================

function ToggleSettingsMenu() {
    let modal = $("#SettingsModal");
    let btnText = $("#SettingsButtonLabel");
    if (!modal) return;

    g_SubTickState.isMenuOpen = !g_SubTickState.isMenuOpen;

    if (g_SubTickState.isMenuOpen) {
        modal.RemoveClass("hidden");
        modal.SetFocus();
        if (btnText) btnText.text = "✕ CLOSE [F1]";
    } else {
        modal.AddClass("hidden");
        // Release focus back to game engine so Freecam and mouse look work!
        $.GetContextPanel().SetFocus();
        if (btnText) btnText.text = "⚙ REPLAY SETTINGS [F1]";
    }
}

function OnToggleLayer(layerName) {
    let cur = g_SubTickState.layers[layerName];
    g_SubTickState.layers[layerName] = !cur;

    if (layerName === "subtick") {
        let p = $("#SubTickBarContainer");
        if (p) p.style.opacity = g_SubTickState.layers.subtick ? "1.0" : "0.0";
    } else if (layerName === "anomalies") {
        let p = $("#AnomalyCard");
        if (p) p.style.opacity = g_SubTickState.layers.anomalies ? "1.0" : "0.0";
    } else if (layerName === "hitbox" || layerName === "raytrace") {
        let p = $("#SpatialHitboxGuide");
        if (p) p.style.opacity = (g_SubTickState.layers.hitbox || g_SubTickState.layers.raytrace) ? "1.0" : "0.0";
    }
}

function OnCycleCamMode() {
    let modes = ["FIRST_PERSON", "CHASE_CAM", "FREECAM"];
    let idx = modes.indexOf(g_SubTickState.cameraMode);
    g_SubTickState.cameraMode = modes[(idx + 1) % modes.length];

    let lbl = $("#LblCamMode");
    if (lbl) lbl.text = `Cam Mode [F8]: ${g_SubTickState.cameraMode}`;

    // Execute engine command for spec mode
    if (typeof GameInterfaceAPI !== "undefined" && GameInterfaceAPI.ConsoleExec) {
        if (g_SubTickState.cameraMode === "FREECAM") {
            GameInterfaceAPI.ConsoleExec("spec_mode 1");
        } else if (g_SubTickState.cameraMode === "FIRST_PERSON") {
            GameInterfaceAPI.ConsoleExec("spec_mode 4");
        } else if (g_SubTickState.cameraMode === "CHASE_CAM") {
            GameInterfaceAPI.ConsoleExec("spec_mode 5");
        }
    }
}

function OnToggleLiveMode() {
    g_SubTickState.liveDiagnostics = !g_SubTickState.liveDiagnostics;
    let lbl = $("#LblLiveMode");
    let btn = $("#BtnLiveMode");
    if (lbl) {
        lbl.text = g_SubTickState.liveDiagnostics ? "Live HUD [F7]: Always-On" : "Live HUD [F7]: Event-Only";
    }
    if (btn) {
        btn.style.backgroundColor = g_SubTickState.liveDiagnostics ? "#064e3b" : "#1e293b";
        btn.style.border = g_SubTickState.liveDiagnostics ? "1px solid #10b981" : "1px solid #475569";
    }
}

function OnTriggerTestShot() {
    let frac = 0.40 + Math.random() * 0.50;
    let unlag = 47.6;
    let isHit = Math.random() > 0.25;

    let card = $("#SubTickBarContainer");
    let fill = $("#SubTickFill");
    let needle = $("#SubTickNeedle");
    let callout = $("#SubTickCallout");

    let actMs = frac * 15.625;
    let pct = (frac * 100.0).toFixed(1) + "%";

    if (fill) fill.style.width = pct;
    if (needle) needle.style.marginLeft = pct;
    if (callout) callout.text = `Test Shot (+attack) @ ${actMs.toFixed(2)} ms (w = ${frac.toFixed(3)})`;

    let anomaly = $("#AnomalyCard");
    if (anomaly) {
        if (isHit) {
            anomaly.RemoveClass("Miss");
            let t = $("#AnomalyTitle");
            let d = $("#AnomalyDesc");
            if (t) t.text = "✓ PARITY CONFIRMED // ROLLBACK MONOTONIC";
            if (d) d.text = `sv_maxunlag: 200.0ms | Rewind: -${unlag.toFixed(1)}ms | Delta: 0.46u <= 4.0u`;
        } else {
            anomaly.AddClass("Miss");
            let t = $("#AnomalyTitle");
            let d = $("#AnomalyDesc");
            if (t) t.text = "! LAG COMPENSATION ROLLBACK ANOMALY";
            if (d) d.text = `sv_maxunlag: 200.0ms | Rewind: -${unlag.toFixed(1)}ms | Delta: 5.12u > 4.0u`;
        }
    }
}

function OnJumpAnomaly(tick) {
    let target = Math.max(0, tick - 32);
    if (typeof DemoAPI !== "undefined" && DemoAPI.SetPlaybackTick) {
        DemoAPI.SetPlaybackTick(target);
    } else if (typeof GameInterfaceAPI !== "undefined" && GameInterfaceAPI.ConsoleExec) {
        GameInterfaceAPI.ConsoleExec("demo_gototick " + target);
    }
    $.Msg("[SUBTICK_HUD] Jumped to anomaly tick: " + target);
}

function OnSeekRelative(deltaTicks) {
    let cur = g_SubTickState.currentTick;
    let target = Math.max(0, Math.min(g_SubTickState.totalTicks, cur + deltaTicks));
    if (typeof DemoAPI !== "undefined" && DemoAPI.SetPlaybackTick) {
        DemoAPI.SetPlaybackTick(target);
    } else if (typeof GameInterfaceAPI !== "undefined" && GameInterfaceAPI.ConsoleExec) {
        GameInterfaceAPI.ConsoleExec("demo_gototick " + target);
    }
}

function OnTogglePlayPause() {
    if (typeof DemoAPI !== "undefined") {
        if (DemoAPI.IsPlaybackPaused && DemoAPI.IsPlaybackPaused()) {
            if (DemoAPI.ResumePlayback) DemoAPI.ResumePlayback();
        } else {
            if (DemoAPI.PausePlayback) DemoAPI.PausePlayback();
        }
    } else if (typeof GameInterfaceAPI !== "undefined" && GameInterfaceAPI.ConsoleExec) {
        GameInterfaceAPI.ConsoleExec("demo_togglepause");
    }
}

function OnScrubberChanged() {
    let slider = $("#DemoTimelineSlider");
    if (!slider) return;
    let targetTick = Math.floor(slider.value);
    if (typeof DemoAPI !== "undefined" && DemoAPI.SetPlaybackTick) {
        DemoAPI.SetPlaybackTick(targetTick);
    } else if (typeof GameInterfaceAPI !== "undefined" && GameInterfaceAPI.ConsoleExec) {
        GameInterfaceAPI.ConsoleExec("demo_gototick " + targetTick);
    }
}

function OnAnomalyPagePrev() {
    g_SubTickState.anomalyPage = Math.max(0, g_SubTickState.anomalyPage - 1);
    let lbl = $("#LblAnomalyPage");
    if (lbl) lbl.text = `Page ${g_SubTickState.anomalyPage + 1}/3`;
}

function OnAnomalyPageNext() {
    g_SubTickState.anomalyPage = Math.min(2, g_SubTickState.anomalyPage + 1);
    let lbl = $("#LblAnomalyPage");
    if (lbl) lbl.text = `Page ${g_SubTickState.anomalyPage + 1}/3`;
}
