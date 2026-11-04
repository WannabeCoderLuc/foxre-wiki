# Soldiers and alert phases in a mod

*Based on: [How soldiers think](../explain/soldier-ai.md). Exact details: [Soldier AI](../engine/soldier-ai.md). M9 PASS (2026-11-04); open points may still change details. Addresses are for 1.0.15.4 EN. Live data comes from `afgh_sovietBase_cp`, with the same chain checked at a second base, `afgh_enemyBase_cp`. Tags: [V] read in code, [D] measured live, [I] inferred, [?] open.*

## The findings
- A CP has a phase: 0 sneak, 1 caution, 2 evasion, 3 alert.
- Waits inside a phase are investigations: the CP sends 3, then 2, then 4 soldiers to one search point, and the next report goes out in the frame an investigator marks the point done [V, D two bases]. A mod that changes how many soldiers investigate, or ends the search early, changes how long alert and evasion last.
- A report lasts as long as its voice line (0x3C and 0x3B 2.45 s, 0x51 about 11.5 s) [V, D].
- The phase falls by itself, one step at a time: alert, then evasion, then caution [V, D].
- Each phase runs one 0-to-1 timer at its own rate: caution 36 minutes, evasion 2 minutes, alert 30 seconds, before multipliers [V, D: read live in every CP].
- Alert's timer has a slow band: between 0.5 and 0.4 it falls 100 times slower while the player is within 10 m of the base's front point, the last place a soldier saw the player (the point moves only when a seen player is more than 10 m from it) [V, D three runs]. A mod that wants a base to calm down after you hide nearby shortens that 10 m or the band; one that wants a longer manhunt widens it.
- A phase ends when the CP's report request finishes, not when the timer hits 0 [V, D two runs].
- `SetPhase` works per CP but takes effect later [D].
- Only **18 soldiers** are fully simulated at once, chosen each frame [V, D].
- Lowering sight distance to 0 does not stop a base noticing you [D, cause not known].

## Reading and setting the phase
```lua
local cp = GameObject.GetGameObjectId("TppCommandPost2", "afgh_sovietBase_cp")
local phase = GameObject.SendCommand(cp, { id = "GetPhase", cpName = "afgh_sovietBase_cp" })
GameObject.SendCommand(cp, { id = "SetPhase", phase = TppGameObject.PHASE_CAUTION })
```
**`SetPhase` is asynchronous.** It writes a *requested* phase, so `GetPhase` in the same call still returns the old value [D]. Wait for the `GameObject.ChangePhase` message rather than reading straight back.

What a forced phase did in our runs [D, base 120 m from the player]:

| Command | Result |
|---|---|
| Caution | Route changes at once; soldier stands, walks, runs to the new route |
| Evasion | Falls to caution on its own after about 26 s (two runs) |
| Alert | Route action stops; dashes and stops. With no known target, this is not a fight |
| Sneak, after alert | Sneak route back at once, but one soldier then stood still 110 m from it for 90 s (one run) [?] |

To hold a phase, Infinite Heaven's `phaseUpdate`, `minPhase`, `maxPhase` and `phaseUpdateRate` re-send `SetPhase` on a timer. Setting max to sneak pulled a commanded caution back within 3 s [D].

## Keeping caution on
```lua
GameObject.SendCommand(cp, { id = "SetKeepCaution", enable = true })
```
This sets a flag and, if the base is below evasion, also requests caution and fills the timer [V 0x140D63510]. Vanilla scripts use it: s10150, and s10070 together with `SetCpForceSiren`. Turn it off with `enable = false`. Whether the flag is what stops the timer draining is not checked [?].

## Changing how long phases last
No vanilla Lua command sets the lengths; they are rates in memory. *The fields were read live by a log-only hook (2026-11-04); writing them has not been tested by us.*

| Field (from the CP impl, `*(self + 0x70)`) | Meaning |
|---|---|
| `+0x28`, stride 0x14, `+4` | Caution rate: default 1/2160 per second |
| same, `+8` | Evasion rate: default 1/120 |
| same, `+0xC` | Alert rate: default 1/30 |
| `+0x30`, stride 0x60, `+0x50` | The timer, 1.0 to 0 |
| `+0x30`, stride 0x60, `+0x48` / `+0x4C` | Current phase / requested phase |
| `+0x158` | Frame time |

Drains: caution `0x140D6E960`, evasion inside state `0x140D708F0`, alert `0x140D6B7E0`.

A wanted length L in seconds means a rate of 1/L **for the timer only**. The phase then still waits for its reports: after alert's timer reaches 0 our runs needed about 31 s more (reports 0x3C and 0x3B), and evasion ended on report 0x3A at 61 s with its timer still at 0.67 [D]. So a faster evasion rate alone will not shorten evasion, and a longer alert rate adds to that 31 s. Requests finish in the callbacks `0x140D6BF00` (alert), `0x140D70370` (evasion), `0x140D6ECC0` (caution). The community's V_Framework `SetCautionPhaseDuration` hooks the caution drain and replaces its amount. It is a community example of this approach; check its addresses in the [claims ledger](claims.md).

## Choosing who is simulated
Each frame the game picks **18** soldiers inside a 640 x 640 m window around the player, inset 32 m to enter and 28 m to stay [V, D]. Closest to the window's centre come first; height counts. So:

- A fight far from the player is simulated only if those soldiers make the list.
- An unrealized soldier does not animate and moves at lower speeds: walk 0.80, run 2.00, dash 4.00 m/s, against 0.975, 2.50, 6.43.
- Adding soldiers past the budget is fine, but only 18 are realized at once.

`SetForceRealize` gives a soldier top priority in the sort [V 0x141356170]. Forcing many works against the budget: others are pushed out. Use it for the one soldier the player must see behave properly.

## Testing near soldiers
These are the rules that made our test runs usable. They apply to a mod's test too:
```lua
Player.ChangeLifeMaxValue(50000)          -- then, once a second:
if vars.playerLife > 0 then vars.playerLife = vars.playerLifeMax end
```

- This held through 45 hits under alert with life unchanged [D]. Do this for tests only.
- **Never save during such a test.** Life, clock and weather live in `vars` and go into the checkpoint. Watch the save file's time.
- `TppClock.SetTime("12:00:00")` and `TppClock.Stop()` keep daylight the same between runs. `TppWeather.ForceRequestWeather(0, 1)` is accepted, but its effect is unconfirmed [?].
- Warp 2 m above the ground ([Ground height at any point](ground-height.md)). A 30 m drop caused fall damage, and terrain may need a moment to load.
- **Sight scale 0 stops sight notice, not alerts already running.** With IH's `soldierSightDistScale` and `soldierHearingDistScale` at 0 a soldier walked within 3.5 m of the player with no notice (one run); set after an alert starts, the player stayed unseen at the spot for 21 to 63 s after the band started, but a soldier saw the player again later in all three runs (`m9_g6d` to `m9_g6f`), so something other than the scaled sight still reports at close range [?]. An older run that still gave an alert ran before the test setup was pinned [I]. Patrol trucks notice you too.
- Don't touch the game during a run, and keep forced-phase runs apart from natural ones. A forced phase changes what follows it.
- Hits push the player. A move over 3 m with no damage message means something else moved them.

## How this would be used in a mod
*Hypothetical example; not built or tested.* A "lockdown" mod makes a base stay on watch for 5 minutes after any fight, and then relax on its own.

1. Listen for `GameObject.ChangePhase` from the CP.
2. When the phase falls to caution, start a 300 s timer and enable `SetKeepCaution`.
3. When the timer ends, disable it and request sneak:
```lua
GameObject.SendCommand(cp, { id = "SetKeepCaution", enable = false })
GameObject.SendCommand(cp, { id = "SetPhase", phase = TppGameObject.PHASE_SNEAK })
```

4. Give guards a tighter route for caution in advance with `SetCautionRoute` ([Navmeshes and routes in a mod](navigation-and-routes.md)).

This uses only Lua commands. Without it, caution would last far longer: its timer alone runs 36 minutes [V, D rate and slope], before its closing report. So simply requesting sneak sooner is also a usable "shorter caution" mod.

Things to check in such a mod: sneak forced after alert left one soldier standing still in our run, and other CPs follow this one's phases (8 other CPs went to caution about 21 s into evasion) [D].

## Pitfalls
- Fight details differ from run to run. Don't time a mod's event from alert length: 58 and 180 s past the player's leaving in two identical runs.
- Alert only starts draining when the CP has lost sight of the player.
- A CP in alert can pull a neighbouring CP into alert when soldiers come within 70 m of each other [V 0x140D67C46]. A "calm" CP may rise for no visible reason.
- The offsets above are for this build. Check before hooking.

---
<small>Hand-written article (`docs/site/mods/Soldier-AI.md`) &middot; published 2026-11-05.</small>
