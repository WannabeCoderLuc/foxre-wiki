# Soldier AI

Far mode, move speeds, route state and CP phase sequences of `TppSoldier2`, f30010. Engine: `Engine/world/realize.py`. Tests: `Engine/tests/test_m9_soldier.py`. Fixtures: `m9_soldier_free.json`, `m9_soldier_forced.json` (`Tools/m9_fixture.py`). Tags: [V] static or exact, [D] measured live, [I] inferred, [?] open.

## Capture protocol
Near soldiers the run must stay readable and the player must not die. `Tools/m9_run.py <name> <plan>` runs one capture end to end (deploy, boot, drive, stop, restore); the driver is `Tools/m9_drive.py`, plans in `Tools/m9_plans/`. Runs live in `Memory/research/m9_*`, apart from `m8_nav14`, `m8_nav15`.

| Measure | How | Status |
|---|---|---|
| Unlimited health | `Player.ChangeLifeMaxValue(50000)`, then life = max once a second, logged each second | **Proven**: 45 hits at 25 m under alert, life stayed 65001/65001, no death (`m9_sb_forced1`) |
| Phase, per CP | `SendCommand(cp, {id="SetPhase", phase=})`, the command IH's clamp uses | **Proven**. Asynchronous: `GetPhase` answers the old value in the same call. Logged as `GameObject.ChangePhase` |
| Phase clamp, global | IH `phaseUpdate` 1, `minPhase`, `maxPhase`, `phaseUpdateRate` | **Proven**: max sneak pulled a commanded caution back in 3 s (`m9_opt2`). Not used in fixtures |
| Clock | `TppClock.SetTime("12:00:00")`, `TppClock.Stop()` | Accepted; read back as set |
| Weather | `TppWeather.ForceRequestWeather(0, 1)` (sunny) | Accepted; the one reading came too soon to show a change, so not confirmed [?] |
| Sight, hearing scale | IH `soldierParamsProfile` 1, `soldierSightDistScale`, `soldierHearingDistScale`, `InfSoldierParams.SoldierParametersMod()` | **Not confirmed, not used**: at 13 m neither scale 0 nor the 100 control noticed (`m9_opt2`), so the test does not separate them. Needs a soldier facing the player |
| Reinforcements | none set: `forceReinforceRequest`, `enableHeliReinforce`, `enableSoldiersWithVehicleReinforce` read 0 | No reinforcement message in the Central Base Camp runs [D]. `SetReinforceEnable` exists, untested |
| Heli and support | IH `disableHeliAttack` exists; no call is ever made | Not tested, nothing to switch off so far |
| Vehicles | The player stands on foot; riders stay in the logs at 8 to 12.5 m/s, without a move bit | Excluded from the speed tables by that rule |
| Warps | 2 m above the terrain from the M7 `HeightField`. A 30 m drop gave fall damage (`m9_free2_falldamage`) | **Proven** |

The driver takes no input and never fires. It stops and marks the run contaminated on: life at 0 or under 10 %, a player move over 3 m after a warp has settled, target dead or neutralized, a checkpoint save during the run, in a free run any phase change or damage, in a forced run the CP rising above the commanded phase. Falling back by itself is the behaviour under test, not a stop.

Rules that came from mistakes:

- **Nobody touches the game during a run.** `m9_humanplay1_contaminated` was played by hand. The 60 m move limit it passed under is now 3 m.
- The game keeps 60 fps without window focus [D], so focus is logged, not a stop; other use of the PC does not spoil a run unless it reaches the game.
- Hits push the player: `m9_sb_forced1` stopped on a 4 m push at the end of the fire test, as it should. Its fixture part ends before that test.
- **Never save during a run.** Life, clock and weather live in `vars` and would go into the checkpoint. The driver watches the save file. A checkpoint written out of bounds put the player at y = -79.2 on every boot; repaired on 2026-11-01 with `TppMission.UpdateCheckPointAtCurrentPosition()` from solid ground with vanilla state (old save: `Backups\saves\20261101_before_spawnfix`). The likely source is the M7 warp drops of 2026-10-29: the save's date matches [I].

## Far mode is the unrealized state [V 0x141551820, D live]
Not a distance. `TppSoldier2RealizerInterface` selects the soldiers to realize each frame:

1. Candidates: enabled soldiers inside the stage window (640 x 640 m, `rect` of the stage block object, 5 x 5 blocks of 128 m), inset by **32 m to enter, 28 m to stay** (in-window bit, pack +0x18 [2]). Height is not tested. Flag word bit 47 (writer not decoded [?]) or an active soldier with +0x1A0 bit 1 is a candidate anywhere.
2. Priority: squared distance to the window centre, float32, centre in whole metres. Height counts; if the +0x28 byte is set, height counts 5 times. Bit 47 = -10000. Already realized with +0x1A0 bit 1, or flag bit 3, 6, 7 or 15 = 0 (`SetForceRealize` sets bit 15 [V 0x141356170]).
3. An unseen soldier beyond 70 m (d² 4900) gets +90000 (300 m squared) when the view test is on (`0x142313048`, `0x142189B04`). Soldiers under 4 m (d² 16) can be left out while flag 0x15 is on and the soldier is not in action state 2 or riding.
4. Sorted, then the first `max` are realized. `max` (+0x24) = **18**, `total` (+0x20) = 330 live (IH's raised count). Slots beyond the first ones swap for soldiers with bit 0x20000 of the second word (at most 6 counted) and reserve the last 2 for soldiers with bit 0x100 within 250 m.

So the "200 m" seen in M8 was the window around the player, not a radius.

**Port:** `select` covers steps 1, 2 and the budget, without the view test, the +0x1A0 byte and the swaps. 159 of 181 live lists give the same set. Every other list differs only within the distance a soldier moves in the sample's age (up to 30 frames; riders 12.5 m/s) of the margin that applies to it, or on the first list after the window moved [D]. A frame-exact capture would settle it. The sort order inside the list is not compared: the realized-first rule needs the +0x1A0 byte.

## Move speeds [D, modal m/s, free and forced runs]
Flag word +0x110, stride 0x28: bits 16 to 23. Bit 0x10 walk, 0x20 run, 0x40 dash [I: names from speed; 0x140ED4C10 classes 1, 2, 3], 0x04 caution, 0x02 idle at a node.

| Bits | Meaning | Realized | Unrealized |
|---|---|---|---|
| 0x10 | walk | 0.975 | **0.80** |
| 0x14 | caution walk | 1.74 | 1.50 |
| 0x20 | run | 2.50 | 2.00 |
| 0x24 | caution run | 4.01 | 2.75 |
| 0x30 | | | 2.00 free, 2.75 forced [?] |
| 0x40, 0x44 | dash | 6.43 | 4.00 |

Realized speed comes from animation; unrealized values look like constants [I]. Their table is not decoded (`TppSoldier2UnrealStepAction`, built in 0x1415A35D0) [?].

## Route state [V fields, D meaning]
Route table at impl +0xE8: +8 u32 current route (StrCode32), +0x10 u32, +0x18 u16, +0x20 u8 state. `IsOnRoute` tests state not 0 and not 3 [V 0x141356170]. `GetUsingRoute` and `GetDoingRouteEventIndex` have only the heli handler [V], which is why they return nil for soldiers.

| State | Meaning [D] |
|---|---|
| 3 | starting a route |
| 0 | on the way to the route |
| 1 | on an edge |
| 2 | at a node, waiting |

Transitions in the free runs: 2>1 468, 1>2 463, 3>2 338, 3>0 173, 0>1 123, 0>2 21, all others 16. +0x10 and +0x18 change with the route [?]; meaning not decoded.

Distance from the route edge while walking in state 1: unrealized p50 0.00, p99 0.21 m; realized p50 0.25, p99 1.98, max 6.5 m. The 18 m of `m8_nav_20261029_185330` did not come back with the player standing and no phase change. It was uncontrolled, so it is not confirmed as route following [?].

`RequestMove` by the state at the next sample (free, slot = soldier index [I]): unrealized state 1 338, state 3 85, state 0 13, state 2 4; realized state 1 60, state 2 1. So requests also come while on an edge, and from far soldiers [?]. **What triggers a request is not decoded.**

## Phases [D, forced, soldier 78, afgh_sovietBase_cp, player 120 m away]
- Sneak: route 1E072FB4, state 2 at the node.
- SetPhase caution: route changes at once to F49C0789, state 0, bits 0x04 then 0x14 then 0x24: stands, walks, runs to the new route. Same in both runs. State 2 on arrival.
- Commanded evasion falls back to caution by itself after about 26 s (both runs); state 3 then 0 or 1, moving again.
- Alert: state 3, dash and stops (bits 0x40, 0x04, 0x00). In forced1 commanded sneak after alert brought the sneak route 1E072FB4 back at once, `IsOnRoute` true in the same second, and the soldier stayed at state 2 where it stood, about 110 m from that route, for the remaining 90 s. Not repeated [?].
- Evasion and alert differ between runs after the first steps, so only the part above is pinned. Without a known target the alert is not a fight.

Forced2 ended at 244 s (reply lost on the pipe, driver now retries and always writes its result), so "after alert" has one run.

Seen in hand play only, not pinned: other CPs went to caution when this CP fell back (`m9_humanplay1_contaminated`) [?].

## Open
- The move table of unrealized soldiers; what +0x10 and +0x18 of the route table hold.
- What starts a path request on a route; node events and waits by event type.
- Sight and hearing scale test with a facing soldier.
- Behaviour with a known target (fire, search), which needs a clean design: the driver stands still and hits push it.
- A second base and Africa; the +0x1A0 byte, the view test and the slot swaps in the port.

---
<small>Source: `docs/engine/SoldierAI.md` in the project repository &middot; generated 2026-11-01.</small>
