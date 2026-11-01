# Soldier AI

Far mode, move speeds, route state and CP phase sequences of `TppSoldier2`, f30010. Engine: `Engine/world/realize.py`, `Engine/world/route_follow.py`. Tests: `Engine/tests/test_m9_soldier.py`, `test_m9_route.py`. Fixtures: `m9_soldier_free.json`, `m9_soldier_forced.json` (`Tools/m9_fixture.py`), `m9_route.json`, `m9_known.json` (`Tools/m9_route_fixture.py`). Tags: [V] static or exact, [D] measured live, [I] inferred, [?] open.

## Capture protocol
Near soldiers the run must stay readable and the player must not die. `Tools/m9_run.py <name> <plan>` runs one capture end to end (deploy, boot, drive, stop, restore); the driver is `Tools/m9_drive.py`, plans in `Tools/m9_plans/`. Runs live in `Memory/research/m9_*`, apart from `m8_nav14`, `m8_nav15`.

| Measure | How | Status |
|---|---|---|
| Unlimited health | `Player.ChangeLifeMaxValue(50000)`, then life = max once a second, logged each second | **Proven**: 45 hits at 25 m under alert, life stayed 65001/65001, no death (`m9_sb_forced1`) |
| Phase, per CP | `SendCommand(cp, {id="SetPhase", phase=})`, the command IH's clamp uses | **Proven**. Asynchronous: `GetPhase` answers the old value in the same call. Logged as `GameObject.ChangePhase` |
| Phase clamp, global | IH `phaseUpdate` 1, `minPhase`, `maxPhase`, `phaseUpdateRate` | **Proven**: max sneak pulled a commanded caution back in 3 s (`m9_opt2`). Not used in fixtures |
| Clock | `TppClock.SetTime("12:00:00")`, `TppClock.Stop()` | Accepted; read back as set |
| Weather | `TppWeather.ForceRequestWeather(0, 1)` (sunny) | Accepted; the one reading came too soon to show a change, so not confirmed [?] |
| Sight, hearing scale | IH `soldierParamsProfile` 1, `soldierSightDistScale`, `soldierHearingDistScale`, `InfSoldierParams.SoldierParametersMod()` | **Does not stop notice, not used**: soldier walking up at 15 m reached alert 19.9 s after the warp at scale 0, 6.1 s at 100 (`m9_sight0`, `m9_sight100`, one run each). Later at 0 [D], but who noticed was not logged, so the cause is not shown [?]. Hearing was not tested: the driver makes no noise |
| Reinforcements | none set: `forceReinforceRequest`, `enableHeliReinforce`, `enableSoldiersWithVehicleReinforce` read 0 | No reinforcement message in the Central Base Camp runs [D]. `SetReinforceEnable` exists, untested |
| Heli and support | IH `disableHeliAttack` exists; no call is ever made | Not tested, nothing to switch off so far |
| Vehicles | The player stands on foot; riders stay in the logs at 8 to 12.5 m/s, without a move bit | Excluded from the speed tables by that rule |
| Warps | 2 m above the terrain from the M7 `HeightField`. A 30 m drop gave fall damage (`m9_free2_falldamage`) | **Proven** |

The driver takes no input and never fires. It stops and marks the run contaminated on: life at 0 or under 10 %, a player move over 3 m after a warp has settled (unless `Player.PlayerDamaged` came within 6 s and the move is at most 15 m: logged as a push), target dead or neutralized, a checkpoint save during the run, in a free run any phase change or damage, in a forced run the CP rising above the commanded phase. Clamp `noticed` lets the CP rise and fall by itself. Falling back by itself is the behaviour under test, not a stop. **The push path has not run yet:** 282 hits in `m9_known1`, `m9_known2` moved the player under 3 m.

Rules that came from mistakes:

- **Nobody touches the game during a run.** `m9_humanplay1_contaminated` was played by hand. The 60 m move limit it passed under is now 3 m.
- The game keeps 60 fps without window focus [D], so focus is logged, not a stop; other use of the PC does not spoil a run unless it reaches the game.
- Hits push the player: `m9_sb_forced1` stopped on a 4 m push at the end of the fire test, as it should. Its fixture part ends before that test.
- Patrol trucks notice the player too: `m9_route2` stopped at 228 s when one drove past (Luc saw it); its fixture part ends there.
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

Realized speed comes from animation; unrealized values look like constants [I]. Their table is not decoded [?]. It is not `TppSoldier2UnrealStepAction` (0x1415940C0): that is a one-off 2 s relocation (state 0x141595B70), holding none of these speeds [V].

## Route step machine [V, D 2 free runs]
Route action plugin (vtables 0x142418930 and siblings; +0x1B0 soldier impl, +0x1C0 move records stride 0x70, +0x1B8 route set). Per-frame update 0x141570FA0 runs the step in the table 0x142C62A30 by record +0x26 with op 3 (update); a changed step, or a restart asked by the step, gets op 1 (leave) on the old one and op 0 (enter) on the new one; 0x14157AF10 then copies the record to the route table.

| Action record | Field |
|---|---|
| +0x00 | step timer |
| +0x14 | route (StrCode32) |
| +0x20 u16 | node index |
| +0x24 u16 | flags; bit 2 ends the route (step 0x10) |
| +0x26, +0x27 u8 | step, previous step |
| +0x2A u8 | event index: 0 on the leg, i during node event i |
| +0x2B u8 | laps |

**Route table at impl +0xE8 [V 0x14157AF10]:** +8 u32 route, +0x10 **u16** node, +0x18 **u8** event index, +0x20 u8 state = move record +0x62. FoxTrace read +0x10 and +0x18 at the wrong widths before 2026-11-02, so those columns of older runs mean nothing.

| Step | State | Function | Meaning |
|---|---|---|---|
| 1 | 0 | 0x14157A130 | first leg to the route: as step 2, with record +0x66 bit 0x20 set |
| 2 | 1 | 0x141578E30 | leg to the node |
| 3 | 2 | 0x141574B90 | node event |
| 4, 5, 0x10 | 1 | | seen rarely, meaning not decoded [?] |

State 3 never appears in these rows: the update does not run then. It holds from boot and through alert and evasion (see Known target), so it means the route action is not active [I], not "starting a route" as written before. `IsOnRoute` = state not 0 and not 3 [V 0x141356170].

**What starts a path request [V, D]:** op 0 (or 4) of steps 1, 2 builds the leg goal (0x14157BC20), then 0x1415713C0 sends **one `RequestMove`, slot = the soldier index**, owner 0xDF31BA77279E. So one request per leg start, realized or not: that is why they come in state 1 and from far soldiers. All 898 soldier requests of both runs return into it (0x14157150C); 12 others have owner 0xA5A1FB6041C7 (0x141344090). 673 of 673 legs of kind 0 sent one in the same frame; 450 of 450 legs of kind 1 (record +0x66 & 3, the vehicle riders 170 to 173) sent none. Request fields:

- +0x78 waypoints 2 when the target node has no node event (the next leg is included, +0x66 bit 0x10), else 1: 673 of 673.
- +0x80 mask 8, +0x84 multiplier 2.0 only with +0x66 bit 0x20 (first legs). The same 94 first-leg requests came at boot in both runs.
- +0x88 5.0 if action +0x3E is -1, else 0; +0x8C 10.0.

A leg ends by the kind's arrival test (0x14156CBD0, 0x14156CF30, 0x14156D1E0); kind 0 reads remaining path length under 5 m [I, the decompile loses the return]. Not ported.

**Order [D]:** `route_follow.step_after` equals every change between steps 2 and 3 of every soldier: 962 and 700 of 700 in the two runs. Leg to a node; its node events in order, except `SwitchRoute` and 0x8706030D, which run without a stop [V 0x14156FDC0]; then the next node, wrapping, laps + 1. A next node at the same spot runs its events with no leg (136 cases at 0 m, legs from 1.64 m; the exact test is not decoded [?]). Record +0x66 bit 0x40 reverses the direction [V 0x141571270], no reversed route was seen live.

**Waits [D]:** node event `time` = frames at 60 per second, whole seconds minus one frame (the community `FRT` page says the same). Live / (time + 1) / 60: median 1.07, under 0.99 in 5 of 594, minimum 0.92. Nearly all node events here are `RelaxedIdleAct` 0xEF94DD47. Why some last much longer (1198 frames: minimum 20 s, median 24.7 s) is not decoded [?].

Distance from the route edge while walking in state 1: unrealized p50 0.00, p99 0.21 m; realized p50 0.25, p99 1.98, max 6.5 m. The 18 m of `m8_nav_20261029_185330` did not come back with the player standing and no phase change. It was uncontrolled, so it is not confirmed as route following [?].

## Known target [D, 2 runs `m9_known1`, `m9_known2`, target soldier 81, afgh_sovietBase_cp]
The driver warps the player 20 m ahead of a walking soldier; no SetPhase. 61 s later it warps 500 m away. Pinned:

- Sneak to alert 6.2 and 6.8 s after the warp. Hits at once (130, 152; life unchanged), none after the player left.
- Then alert, evasion, caution, in that order, by itself. Caution held to the end of the run (214, 110 s): no return to sneak seen.
- 8 other CPs go to caution together 21 and 22 s after this CP enters evasion.
- The target: route state 3 from the alert until caution, route 7DA571CF still stored. At caution a new route E99EB6C3, state 0, then 2 and 1 in turn.

**Not pinned, differs between runs:** alert lasted 58 and 180 s past the player's leaving; evasion 59 and 42 s (commanded evasion: about 26 s); the move bits during the fight.

## CP phase timers (static decode 2026-11-01, not yet logged live)
Each CP has one **normalized timer, 1.0 down to 0**, not seconds. Offsets are from the CP impl (`*(state object +0x70)`). Nothing here has been read from a running game: the rule below predicts, the runs still have to confirm.

| Impl field | Meaning [V unless tagged] |
|---|---|
| +0x28, stride 0x14 | Rates per second: +4 caution, +8 evasion, +0xC alert; +0x10 u16, +0x12 u8 (reinforce count inputs, 0x140D6BCB0) |
| +0x30, stride 0x60 | CP phase record: +0x00 last known position per player (stride 0x10, 4 players), +0x40 known-player mask, +0x44 currently seen mask, +0x48 phase, +0x4C requested phase, +0x50 **timer**, +0x54 and +0x58 flags |
| +0x158 | frame time |
| +0x176 bit 0 | CP-wide mode flag; picks other multipliers. Meaning not decoded [?] |

**Base rates** [V 0x140D5CC81, template at setup object +0x2B0; per-CP copy loop 0x140D5D02C, the copy target is read from the loop only [I]]:

| Phase | Rate | Base length | Drain | Ends by |
|---|---|---|---|---|
| Caution (1) | 0x39F2B9D6 = 1/2160 | **2160 s (36 min)** | 0x140D6E960 | 0x140D6EAA0 writes +0x4C = 0 |
| Evasion (2) | 0x3C088889 = 1/120 | **120 s** | 0x140D6FD90 | 0x140D6FFD0 writes +0x4C = 1 |
| Alert (3) | 0x3D088889 = 1/30 | **30 s** | 0x140D6B7E0 | 0x140D6BBA0 writes +0x4C = 2 |

Caution's 36 minutes fits "caution held 214 s or more" [I: the timer's start value was not logged]. No script timer is involved. The retired V_Framework's `SetCautionPhaseDuration` hooks this same drain and replaces its amount.

**Alert drain 0x140D6B7E0** (runs only while +0x44 = 0; otherwise the state update holds the timer at 1.0, 0x140D6CA20). Rate x frame time, then:

- **Slow band: timer in (0.4, 0.5)** when `vt+0x98` is false and either the player is within 10 m (d² < 100, height under 2 m) of the point at `vt+0x138` +0x254, or state record +4 bit 7 is set: x 0.1 if impl +0x176 bit 0; else x 0.025 if `(impl+0x18)->vt+0xA8(idx, 0)` returned 0; else x 0.01. Crossing that 0.1 of the timer then takes 30, 120 or 300 s instead of 3 s.
- Impl +0x54 bit 18 puts the rate back to base.
- Player state test (0x140D5DEE0 kinds 0x47, 0x6E, 0x80, or 0x140D69F60 with +0xC8 bit 6 clear): x 1.2 if +0x176 bit 0, else x 2.
- `vt+0x98` true: x 1.5.
- State record +4 bit 0x20000 clear: timer goes straight to 0.

**Why alert varies [I, not measured]:** alert past the player's leaving was 58 and 180 s. The band gives 27 + 30 = 57 s or 27 + 120 = 147 s plus the time +0x44 takes to clear. The first is close, the second needs a further 33 s. The run must log which multiplier applied.

**Evasion drain 0x140D6FD90:** state record bit 6 clear: timer 0 at once. Otherwise base rate; x 20 or x 10 by the member byte (impl +0x80, stride 0x1C, +0x16) and record bit 2; the same player state test x 3 (x 1.2 with +0x176 bit 0); +0x54 bit 18 back to base. So 6, 12 or 120 s from the table, none of which equals the measured 26, 42, 59 s. **Evasion is not explained** [?]: the evasion state's own writes (timer capped to 0.07, 0x140D709A6, with +0x54 bit 18) and its start value need the live log.

**Caution drain 0x140D6E960:** runs only if state record +4 bit 31 is set, else timer 0 at once. Skipped while `vt+0xE8` answers true. A true answer from system `Quark +0x98 +0xF8` (query 8) makes it skip one update and set record bit 0x20.

**States:** each phase has a table of state functions `(self, cp, op, record, out)`: op 0 enter, 1 leave, 2 update, 3 check next (out = state, changed). Alert 0x142C3E150: 0x140D6CA20, 0x140D6D240, 0x140D6D4D0. Other tables: 0x142C3E118, 0x142C3E188 (caution), 0x142C3E1B8 (evasion), 0x142C3E1F0. In alert: timer at 0 goes to state 1; there a seen player or timer > 0.1 sets timer 1.0 and returns to state 0.

**Raising the timer:** 0x140D6DA69 adds 0.5 (cap 1.0) when the record's +8 countdown has run out and `vt+0xF0` is true; it then sets the countdowns to 5 s and 60 s. Its gates: timer at least 0.1 and at most 0.5 [V 0x140D6D9FB].

**Other alert source:** 0x140D67C46: a CP in alert with its timer at 0.7 or more can alert another: if active members of the two come within 70 m (d² 4900; another limit if flag bit 24), the other CP gets +0x40, +0x44 bits and +0x4C = 3. This may hold a fight open after the player has left [I].

**`SetKeepCaution` true (0x140D63510):** sets bit 0 of record +0x79 (table impl +0x1E0, stride 0x80), and if that record's phase is under 2, requests caution and sets the timer to 1.0. Whether `vt+0xE8` reads this bit is not checked [?].

**0x140D6DCF0 (180 s and 20 s)** is not the phase timer. It runs a separate countdown at state object +0x78, stride 0x30, +0x20, tied to reinforcement: 180 s, or 20 s if the +0x2A count is nonzero; 5 s and 30 s on its other paths.

**Live logging plan:** hook the state functions above for the impl pointer and state changes, poll the phase record each frame in `h_FrameJob`, hook `AddNoticeInfo` 0x1414DBA80 for who noticed.

## Phases [D, forced, soldier 78, afgh_sovietBase_cp, player 120 m away]
- Sneak: route 1E072FB4, state 2 at the node.
- SetPhase caution: route changes at once to F49C0789, state 0, bits 0x04 then 0x14 then 0x24: stands, walks, runs to the new route. Same in both runs. State 2 on arrival.
- Commanded evasion falls back to caution by itself after about 26 s (both runs); state 3 then 0 or 1, moving again.
- Alert: state 3, dash and stops (bits 0x40, 0x04, 0x00). In forced1 commanded sneak after alert brought the sneak route 1E072FB4 back at once, `IsOnRoute` true in the same second, and the soldier stayed at state 2 where it stood, about 110 m from that route, for the remaining 90 s. Not repeated [?].
- Evasion and alert differ between runs after the first steps, so only the part above is pinned. Without a known target the alert is not a fight.

Forced2 ended at 244 s (reply lost on the pipe, driver now retries and always writes its result), so "after alert" has one run.

Seen in hand play only, not pinned: other CPs went to caution when this CP fell back (`m9_humanplay1_contaminated`) [?].

## Open
- The move table of unrealized soldiers; bits 0x30.
- Phase lengths: base rates and alert multipliers decoded statically; not read live, not ported. Evasion's measured lengths do not fit the table. Who noticed; whether `SetKeepCaution` feeds `vt+0xE8`.
- Node waits longer than `time`; steps 4, 5, 0x10; the same-spot test; arrival tests in the port.
- Sight scale at 0 with who noticed logged; hearing, which needs a noise source; the hit-push path of the driver.
- A second base and Africa; the +0x1A0 byte (0 on all soldiers in the last 20 samples of `m9_route1`), the view test and the slot swaps in the port.

---
<small>Source: `docs/engine/SoldierAI.md` in the project repository &middot; generated 2026-11-01.</small>
