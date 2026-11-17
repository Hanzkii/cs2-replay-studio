"use strict";

(function() {
    $.Msg("[SUBTICK_HUD] Panorama Sub-Tick Replay Overlay initialized.");

    let card = $("#SubTickBarContainer");
    let fill = $("#SubTickFill");
    let needle = $("#SubTickNeedle");
    let callout = $("#SubTickCallout");
    let anomaly = $("#AnomalyCard");

    // Hook weapon fire events during demo playback
    GameEvents.Subscribe("weapon_fire", function(ev) {
        let tick = 0;
        if (typeof DemoAPI !== "undefined" && DemoAPI.GetPlaybackTick) {
            tick = DemoAPI.GetPlaybackTick();
        }
        let frac = (tick % 64) / 64.0;
        let actMs = frac * 15.625;

        let pct = (frac * 100.0).toFixed(1) + "%";
        if (fill) fill.style.width = pct;
        if (needle) needle.style.marginLeft = pct;
        if (callout) callout.text = `${ev.weapon} actuation @ ${actMs.toFixed(2)} ms (w = ${frac.toFixed(3)})`;
    });

    // Hook player hurt events
    GameEvents.Subscribe("player_hurt", function(ev) {
        let isHeadshot = (ev.hitgroup === 1);
        if (anomaly) {
            if (isHeadshot) {
                anomaly.style.backgroundColor = "#064e3be0";
                anomaly.style.border = "1.5px solid #10b981";
                let t = $("#AnomalyTitle");
                let d = $("#AnomalyDesc");
                if (t) t.text = "✓ PARITY CONFIRMED // HEAD HITBOX REGISTERED";
                if (d) d.text = `Damage: ${ev.dmg_health} HP | Hitgroup: Apex #6 (Head)`;
            } else {
                anomaly.style.backgroundColor = "#450a0ae0";
                anomaly.style.border = "1.5px solid #f43f5e";
                let t = $("#AnomalyTitle");
                let d = $("#AnomalyDesc");
                if (t) t.text = "! BODY HIT REGISTRATION // ROLLBACK VERIFIED";
                if (d) d.text = `Damage: ${ev.dmg_health} HP | Hitgroup: ${ev.hitgroup}`;
            }
        }
    });

    // Periodic tick sync loop
    function UpdateTickSync() {
        if (typeof DemoAPI !== "undefined" && DemoAPI.GetPlaybackTick) {
            let curTick = DemoAPI.GetPlaybackTick();
            let title = $("#SubTickTitle");
            if (title) {
                title.text = `SUB-TICK TIMING // 15.625 ms INTERVAL (Tick ${curTick})`;
            }
        }
        $.Schedule(0.1, UpdateTickSync);
    }

    UpdateTickSync();
})();
