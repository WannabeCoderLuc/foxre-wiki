# Soldier AI

Far mode, move speeds, route state and CP phase sequences of `TppSoldier2`, f30010. Engine: `Engine/world/realize.py`, `Engine/world/route_follow.py`. Tests: `Engine/tests/test_m9_soldier.py`, `test_m9_route.py`. Fixtures: `m9_soldier_free.json`, `m9_soldier_forced.json` (`Tools/m9_fixture.py`), `m9_route.json`, `m9_known.json` (`Tools/m9_route_fixture.py`), `m9_phase.json` (`Tools/m9_phase_fixture.py`), `m9_radio.json`, `m9_g5_enemyBase.json` (`Tools/m9_radio_fixture.py`); phase port `Engine/world/cp_phase.py`, tests `test_m9_phase.py`, `test_m9_radio.py`, `test_m9_g5.py`; G4 `m9_g4_route.json` (`Tools/m9_g4_fixture.py`), `test_m9_g4.py`; G6 `m9_g6_band.json` (`Tools/m9_g6_fixture.py`), `test_m9_g6.py`. Names marked [dev] come from the 2015 dev build mapped onto this exe (`GeminiWork/decomp/mgsv.db`, build sha256 = ours); a [dev] name counts only where the retail body was read and matches. Tags: [V] static or exact, [D] measured live, [I] inferred, [?] open.

## Capture protocol
Near soldiers the run must stay readable and the player must not die. `Tools/m9_run.py <name> <plan>` runs one capture end to end (deploy, boot, drive, stop, restore); the driver is `Tools/m9_drive.py`, plans in `Tools/m9_plans/`. Runs live in `Memory/research/m9_*`, apart from `m8_nav14`, `m8_nav15`.

| Measure | How | Status |
|---|---|---|
| Unlimited health | `Player.ChangeLifeMaxValue(50000)`, then life = max once a second, logged each second | **Proven**: 45 hits at 25 m under alert, life stayed 65001/65001, no death (`m9_sb_forced1`) |
| Phase, per CP | `SendCommand(cp, {id="SetPhase", phase=})`, the command IH's clamp uses | **Proven**. Asynchronous: `GetPhase` answers the old value in the same call. Logged as `GameObject.ChangePhase` |
| Phase clamp, global | IH `phaseUpdate` 1, `minPhase`, `maxPhase`, `phaseUpdateRate` | **Proven**: max sneak pulled a commanded caution back in 3 s (`m9_opt2`). Not used in fixtures |
| Clock | `TppClock.SetTime("12:00:00")`, `TppClock.Stop()` | Accepted; read back as set |
| Weather | `TppWeather.ForceRequestWeather(0, 1)` (sunny) | Accepted; the one reading came too soon to show a change, so not confirmed [?] |
| Sight, hearing scale | IH `soldierParamsProfile` 1, `soldierSightDistScale`, `soldierHearingDistScale`, `InfSoldierParams.SoldierParametersMod()` | **Scale 0 stops sight notice in the pinned setup [D one run each, notice log, 2026-11-04]**: `m9_sight0n`: soldier 81 walked up to 3.5 m of the player and past, **no AddNoticeInfo call from any soldier**, CP stayed sneak 60 s. `m9_sight100n`: soldier 81 alone, kind 0 (sight) 0.52 s after the 15 m warp, kind 55 at 4.58 s, alert the next frame. The older `m9_sight0` alert (19.9 s) ran before the save / IH setup was pinned [I: likely cause, not proven]. Not used in fixtures. Hearing not tested: the driver makes no noise |
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
- **The save and IH settings are part of the setup (2026-11-04).** A save that starts in the heli drops the warp and flies the player (stopped `m9_phase1` at 18 s); a night checkpoint gives night routes (soldier 81 stood on `rt_sovietBase_snp_0002n`); IH route-set randomisation, CP subtype and revenge options moved soldier 81 to a sniper route. Runs need `ih_save.lua` = `Backups\ih_save\20261101_opt_test` and the checkpoint at (1040, 322.5, 1214.5) at 12:00, written with `UpdateCheckPointAtCurrentPosition()` outside a run.
- **Checkpoint traps (2026-11-04).** Each base has a `trap_CHK_<base>` ring of 10 m wide box walls (village: about 227 m around (492, 1126); enemyBase: 190 to 280 m around (-535, 544)). A warp that lands inside a wall writes a checkpoint (`m9_village2`: warp to (727, 326, 1177), save at 13.8 s; save repaired with `UpdateCheckPointAtCurrentPosition()` at the spawn spot, now (1039.97, 322.35, 1215.65), backup of the bad one `Backups\saves\20261104_village2_checkpoint_contaminated`). Plans now disable the checkpoints first (`TppCheckPoint.Disable{baseName=...}`, svars only, never saved); it left 26 still enabled, so warps also go to proven points.
- **Pick the soldier from a log, not a recon snapshot.** `sol_village_0000` was running to its post at boot in `m9_village1`; it holds a fixed post (two nodes at one spot), so `m9_village3` found it standing and stopped. `Tools/m9_recon.py` lists soldiers; legs and closest approach come from a FoxTrace run.
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

Realized speed comes from animation. **Unrealized speed [V 0x14139D600, `UnrealBasicAction2Impl::GetMoveVelocityForUnreal` [dev], retail = dev instruction for instruction]:** `(soldier, phase, speed, flag)`, called by ProcessMove (0x1413A1270) with phase = action task (+0x68 table, stride 0xD0) +0xC2 >> 6 & 3, speed = +0xC2 >> 3 & 7, flag = Work +0x1E bit 0. The values are separate float constants, not a table (why the table search failed):

| | speed 1 | speed 2 | speed 3 | other |
|---|---|---|---|---|
| phase 0 | 0.8 | 2.0 | 2.6 | as flag row |
| phase 1 | 1.5 | 2.75 | 4.0 | as flag row |
| phase 2, 3 | as flag row | | | |
| flag row (flag set; else all 1.0) | 1.5 | 2.75 | 4.0 | 1.0 |

Times 0.77197 (0x1423EBD58) when the move record (+0x60 +0x98, stride 0x70) +0x34 & 0x700 = 0x300. Port `realize.unreal_move_speed`. Every measured unrealized speed is in the table; 2.6 was not seen live. Which flag-word bits give which (phase, speed) is not read live [I]: 0x30 at 2.0 free and 2.75 forced fits speed 2 in phase 0 and 1. `TppSoldier2UnrealStepAction` (0x1415940C0) is a one-off 2 s relocation, holding none of these [V].

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
| 4 | 1 | 0x1415784E0 | board the soldier's vehicle (object type 50) or walker gear (type 45): action command 0x19 / 0x1C, record +0x66 kind bits 1 / 2 set [V] |
| 5 | 1 | 0x141578830 | leave it: clears kind bits (+0x66 & 3) [V] |
| 0x10 | 1 | 0x1415784A0 `StepFinishTravel` [dev EXACT] | the route ended (record +0x24 bit 1): idle until the travel plan changes (0x1415707A0), then step 0x12 [V] |

**Step table [V static init 0x142042D60]:** 0 and 0x12 empty; 1 MoveToRoute, 2 MoveToNextNode, 3 Event, 4 / 5 above, 6 BringPlayerWarning, 7 WaitHostage, 8 0x14157A240, 9 0x141579C80, 0xA 0x14157ADA0, 0xB OutOfRain, 0xC 0x141578C20, 0xD PickUpHoneyBee, 0xE MoveToParkWalkerGear, 0xF GetOutWalkerGear, 0x10 FinishTravel, 0x11 NoticeTurn (names [dev], 8 / 9 / 0xA / 0xC unnamed). Steps 4 and 5 are entered from the leg (0x141578E30, ride state 3 and no seat: 5) and from the node handling 0x14156C2A0 (ride interface vt+0xF8 says board: 4); both return to the previous step (+0x27) once the action record's +0x19E bit 0x10 is clear.

State 3 never appears in these rows: the update does not run then. It holds from boot and through alert and evasion (see Known target), so it means the route action is not active [I], not "starting a route" as written before. `IsOnRoute` = state not 0 and not 3 [V 0x141356170].

**What starts a path request [V, D]:** op 0 (or 4) of steps 1, 2 builds the leg goal (0x14157BC20), then 0x1415713C0 sends **one `RequestMove`, slot = the soldier index**, owner 0xDF31BA77279E. So one request per leg start, realized or not: that is why they come in state 1 and from far soldiers. All 898 soldier requests of both runs return into it (0x14157150C); 12 others have owner 0xA5A1FB6041C7 (0x141344090). 673 of 673 legs of kind 0 sent one in the same frame; 450 of 450 legs of kind 1 (record +0x66 & 3, the vehicle riders 170 to 173) sent none. Request fields:

- +0x78 waypoints 2 when the target node has no node event (the next leg is included, +0x66 bit 0x10), else 1: 673 of 673.
- +0x80 mask 8, +0x84 multiplier 2.0 only with +0x66 bit 0x20 (first legs). The same 94 first-leg requests came at boot in both runs.
- +0x88 5.0 if action +0x3E is -1, else 0; +0x8C 10.0.

A leg ends by the kind's arrival test, table 0x142C62BF0 by record +0x66 & 3 (static init 0x142042C30) [V]: **kind 0 (foot) 0x14156CBD0 = remaining path length (path follower vt+0xB0) < 0.25 m** (0x1420F8278); with a target object in record +0xC (soldier or hostage types) and remaining < 5 m (0x142106D34), min(remaining, |target - soldier|) < 0.25 [V, disassembly; the 5 m is only this gate]. Kind 2 (walker gear) 0x14156D1E0 = remaining < 1.0 m. Kind 1 (vehicle) 0x14156CF30 is a distance test with seat states, not ported [?]. Port `route_follow.arrived`.

**Same spot [V 0x14156B120 `CheckAlreadyReachRouteNode` hint]:** after the last node event, the node advances (0x141571270); if the route ended (+0x24 bit 1) step 0x10, else the next node's events run with no leg when the squared 3D distance **from the soldier's current position** to that node is < 1.0 (float32, 0x1420A72CC). Pass-through, vehicle and walker-gear get-in, hostage put-in / take-out and bed nodes always get a leg; soldiers with flag bit 15 of the +0x110 word test the event instead (hash 0x4A6C45E5). After a leg the test is not made. Port `route_follow.already_at`.

**Order [D]:** `route_follow.step_after` equals every change between steps 2 and 3 of every soldier: 962 and 700 of 700 in the two runs. Leg to a node; its node events in order, except `SwitchRoute` and 0x8706030D, which run without a stop [V 0x14156FDC0]; then the next node, wrapping, laps + 1. A next node at the same spot runs its events with no leg (136 cases at 0 m, legs from 1.64 m; the exact test is not decoded [?]). Record +0x66 bit 0x40 reverses the direction [V 0x141571270], no reversed route was seen live.

**Waits [D]:** node event `time` = frames at 60 per second, whole seconds minus one frame (the community `FRT` page says the same). Live / (time + 1) / 60: median 1.07, under 0.99 in 5 of 594, minimum 0.92. Nearly all node events here are `RelaxedIdleAct` 0xEF94DD47.

## Node waits (G4) [V 0x141574B90, 0x14148D150; D runs `m9_g4b`, `m9_g4c`, FoxTrace 3.4]
Runs: `m9_g4b`, `m9_g4c` (plan `sb_g4_near`: player 150 m for 15 s, then IH sight / hearing scale 0, then standing 30 m from soldier 78 for 300 s; free clamp, no phase change, ih_save unchanged after each). `m9_g4a` (same place without the scale, 75 m) went to alert 27 s after the warp and is kept as contaminated. FoxTrace 3.4: `rstep` + `ev` (record +0x28) and `act` (action record +0x19E), new `idleact` (state enter / leave with time left).

A node event ends in one of two ways, set at its start in record +0x28 bit 0 (`route_follow.event_done`):

- **Timer mode** (bit 0 clear): op 3 ends it when the step timer (+0x00, seconds, + frame time each frame in PreUpdate 0x141570FA0) passes the event's `time`.
- **Action mode** (bit 0 set, every acting event incl. `RelaxedIdleAct`, `RelaxedStandIdle`, and the caution replacement `CautionStandIdle` with phase > 0): the route sends one action command (kind 0x11 = `IdleActingActionImpl`, time = the event's `time`) and the event ends **the frame after the action record's +0x19E bit 0x10 clears**. 443 of 456 node-event rows in `m9_g4b` are action mode.

`IdleActingActionImpl` [dev EXACT names, retail bodies read] runs states from table 0x142C5FA80 (static init 0x14203C1F0): 1 StandIdle, 2 single action (0x141487350), 3 / 4 / 5 SmokingStart / Smoking / SmokingEnd, 0xE-0x10 HandSignStop, 0x11 Conversation, 0x13-0x15 Binocular start / act / end (6-0xD, 0x12 unnamed). The first state comes from task +0x22 / +4 (`SelectNextStateFuncIndex` 0x141486000; smoking is skipped in rain or a sandstorm), port `route_follow.idle_act_first_state`. **StandIdle** (0x14148D150): time left (work +0x28) -= the soldier's frame time x the time scale each frame; at <= 0 the task completes. A second countdown (+0x30, set in SetUp 0x1414865C0 to rand x 3.0 + task +0xC, cut to rand x time if longer than the time) starts a single action (state 2, picked by impl +0x158 by act id, rain adds 0x200) and the time left is **frozen** until the soldier is back in StandIdle.

So **wait = start lag + `time` (in StandIdle) + the single actions played on the way + 1 frame**. Live, both runs (86 and 87 action-mode events): time left equal on entry and exit of every non-StandIdle span; every event ended 1 frame after StandIdle left at <= 0; StandIdle frames / (time x 60) 0.96 to 1.04 (the soldier's frame time, not frames, counts); start lag + spans + 1 = the event's length exactly. Single actions (106 and 109) last up to 18.2 s, median 7.8 s. That is the "1198 frames last 20 to 38 s" of `m9_route1`: 20 s of StandIdle plus the single actions played during it. The single-action lengths are their animations (M16 data) and their start times are random (`rand x 3.0`), so the engine can pin the rule but not each run's length [I: the random source vt+0x50 not read]. In both runs one event was cut by a conversation (notice kind 60 to soldiers 84 and 261 at frame 11151 / 11127, state 0x11 after it): the act restarted with time 0 and the route took soldier 261 to a new route. Order of legs and events (same-spot test from the soldier's sampled position): 945 and 947 of 945 and 947 changes; the next node's events ran with no leg once (`m9_g4b`).

**Arrival live:** at a leg's arrival the soldier stands 0.25 m (median, x-z) from the node, which sits 0.25 m above the soldier's position; at most 0.25 m + one walking frame per frame of sample age + 1 (both runs): the 0.25 m remaining-path test. **Steps 4 / 5 / 0x10 live:** step 4 only on the truck crew (soldiers 180, 181, kind 1) at their first route, back to 2 after it; 0x10 at the last node of a route for about 82 frames, then a new route (step 1, 2, or 5 to leave the truck).

Distance from the route edge while walking in state 1: unrealized p50 0.00, p99 0.21 m; realized p50 0.25, p99 1.98, max 6.5 m. The 18 m of `m8_nav_20261029_185330` did not come back with the player standing and no phase change. It was uncontrolled, so it is not confirmed as route following [?].

## Known target [D, 2 runs `m9_known1`, `m9_known2`, target soldier 81, afgh_sovietBase_cp]
The driver warps the player 20 m ahead of a walking soldier; no SetPhase. 61 s later it warps 500 m away. Pinned:

- Sneak to alert 6.2 and 6.8 s after the warp. Hits at once (130, 152; life unchanged), none after the player left.
- Then alert, evasion, caution, in that order, by itself. Caution held to the end of the run (214, 110 s): no return to sneak seen.
- 8 other CPs go to caution together 21 and 22 s after this CP enters evasion.
- The target: route state 3 from the alert until caution, route 7DA571CF still stored. At caution a new route E99EB6C3, state 0, then 2 and 1 in turn.

**Not pinned, differs between runs:** alert lasted 58 and 180 s past the player's leaving; evasion 59 and 42 s (commanded evasion: about 26 s); the move bits during the fight. `m9_phase1`, `m9_phase2` (same plan, request log) agree within 0.8 s: see "CP phase timers".

## CP phase timers [V static, D live 2026-11-04: runs `m9_phase1`, `m9_phase2`, CP index 39 = afgh_sovietBase_cp]
Each CP has one **normalized timer, 1.0 down to 0**, not seconds. Offsets are from the CP impl (`*(state object +0x70)`). FoxTrace `cpphase` hooks the state functions and polls the record; `notice` hooks AddNoticeInfo (FoxTrace 3.1).

**The rule [V, D two runs]: a phase falls back when a CP request it sent has finished, not when its timer runs out.** Requests are sent by impl vt+0x30 (0x140D62660, returns a u16 handle) or `impl+0x18` vt+0x60 (0x140D733F0); on message 0xCE56A00E a per-phase callback switches on the finished id: alert 0x140D6BF00, caution 0x140D6ECC0, evasion 0x140D70370, a fourth 0x140D81CA0 (not identified [?]). The timer only decides when a phase starts asking. Request durations are radio and report lengths (not decoded [?]), which is why phase lengths differed between the older runs.

| Step (player gone, multiplier 1) | Run 1 | Run 2 | Source |
|---|---|---|---|
| Alert: timer held at 1.0 while seen (+0x44 set) | 62 s | 62 s | [V 0x140D6CA20, D] |
| Alert drain 1.0 -> 0 at 1/30 x dt, float32, stops at the first value <= 0 | 1798 frames | 1798 frames | [D bit-exact] |
| State 1 sends 0x3C; finished -> state 2 (1 frame) | 4.5 s | 3.7 s | [V 0x140D6D240, D] |
| State 2 waits while record +4 bit 7 is set, then sends 0x3B; 0x3B finished with timer < 0.8 -> +0x4C = 2 (1 frame) | 21.1 + 5.2 s | 21.2 + 5.2 s | [V 0x140D6D4D0, 0x140D6BF00 case 0x3B; D] |
| Evasion: sends 0x51, its finish sends 0x53; 0x3A finished -> +0x4C = 1 (1 frame), timer still 0.67 | 3684 frames | 3684 frames | [V 0x140D70370 cases 0x51, 0x3A; D] |
| Caution drain at 1/2160 x dt (36 min), then 0x39 | x1.003 slope | x1.003 | [V 0x140D6F480, D slope] |

So alert past the player's leaving = 30 s + about 4 s + 21 s + 5 s = 60.8 s in both runs, the 58 s of `m9_known1`. The 21 s and the evasion length are soldier work, not timers: see "Radio and member roles". The 180 s alert of `m9_known2` (unlogged) is open [?]. Alert sends 0x3D on entry (finished 8.4 s later, no phase effect seen).

Phase state tables [V static initialisers 0x142014A70 ...]: 0x142C3E118 {0x140D68F80, 0x140D694D0, 0x140D69000} is **not sneak** but the CP radio player (`ActionControllerImpl` [dev]: state 1 `StateWaitForCompanion`, state 2 `StateRadio`; FoxTrace logs it as table 0), its finish 0x140D68D60 posts `RadioEnd`, alert 0x142C3E150 {0x140D6CA20, 0x140D6D240, 0x140D6D4D0}, caution 0x142C3E188 {0x140D6F210, 0x140D6F480}, evasion 0x142C3E1B8 {0x140D708F0, 0x140D70CC0}; entries are 16 bytes. 0x142C3E1F0 is not a state table (0x140D71900 takes 3 arguments). State record (argument 4): +0 u16 flags (evasion bits 6, 2), +4 u32 flags, +8 float time in state.

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

Live: every CP of both runs holds exactly these three rates [D]. Caution's timer starts at 1.0 and drains at x1 [D], so 36 minutes before it starts asking (0x39). No script timer is involved. The retired V_Framework's `SetCautionPhaseDuration` hooks this same drain and replaces its amount.

**Alert drain 0x140D6B7E0** (runs only while +0x44 = 0; otherwise the state update holds the timer at 1.0, 0x140D6CA20). Rate x frame time, then:

- **Slow band: timer in (0.4, 0.5)** when `vt+0x98` is false and either the player (while its bit is set in the known mask +0x40) is within 10 m (|dy| < 2 first, then d² < 100) of the CP system's front point (impl +0x5D8, see "Alert slow band (G6)"), or state record +4 bit 7 is set: x 0.1 if impl +0x176 bit 0; else x 0.025 if `(impl+0x18)->vt+0xA8(idx, 0)` returned 0; else x 0.01. Crossing that 0.1 of the timer then takes 30, 120 or 300 s instead of 3 s.
- Impl +0x54 bit 18 puts the rate back to base.
- Player state test (0x140D5DEE0 kinds 0x47, 0x6E, 0x80, or 0x140D69F60 with +0xC8 bit 6 clear): x 1.2 if +0x176 bit 0, else x 2.
- `vt+0x98` true: x 1.5.
- State record +4 bit 0x20000 clear: timer goes straight to 0.

**Which multiplier applied [D]:** with the player 500 m away the drain is plain 1/30 per second, bit-exact (`m9_phase1/2`). The slow band x0.01 is pinned in `m9_g6d`, `m9_g6e` (below); the x2 / x1.5 cases are still static only.

**Evasion drain 0x140D6FD90:** state record bit 6 clear: timer 0 at once. Otherwise base rate; x 20 or x 10 by the member byte (impl +0x80, stride 0x1C, +0x16) and record bit 2; the same player state test x 3 (x 1.2 with +0x176 bit 0); +0x54 bit 18 back to base. The drain runs inside evasion state 0's update (0x140D708F0 op 2): x 20 unless the member byte has bit 0x40, else x 10 unless record +0 bit 2 is set, else x 1. Live record +0 = 0xEF (bits 6 and 2 set): **x 1, 120 s** [D]. **Evasion is explained by the request rule above** (61.4 s, ended at timer 0.67); the 26 s of commanded evasion and the 59 / 42 s of `m9_known` came without a request log [?].

**Caution drain 0x140D6E960:** runs only if state record +4 bit 31 is set, else timer 0 at once. Skipped while `vt+0xE8` answers true. A true answer from system `Quark +0x98 +0xF8` (query 8) makes it skip one update and set record bit 0x20.

**States:** each phase has a table of state functions `(self, cp, op, record, out)`: op 0 enter, 1 leave, 2 update, 3 check next (out = state, changed). Alert 0x142C3E150: 0x140D6CA20, 0x140D6D240, 0x140D6D4D0. Other tables: 0x142C3E118, 0x142C3E188 (caution), 0x142C3E1B8 (evasion), 0x142C3E1F0. In alert: timer at 0 goes to state 1; there a seen player or timer > 0.1 sets timer 1.0 and returns to state 0.

**Raising the timer:** 0x140D6DA69 adds 0.5 (cap 1.0) when the record's +8 countdown has run out and `vt+0xF0` is true; it then sets the countdowns to 5 s and 60 s. Its gates: timer at least 0.1 and at most 0.5 [V 0x140D6D9FB].

**Other alert source:** 0x140D67C46: a CP in alert with its timer at 0.7 or more can alert another: if active members of the two come within 70 m (d² 4900; another limit if flag bit 24), the other CP gets +0x40, +0x44 bits and +0x4C = 3. This may hold a fight open after the player has left [I].

**`SetKeepCaution` true (0x140D63510):** sets bit 0 of record +0x79 (table impl +0x1E0, stride 0x80), and if that record's phase is under 2, requests caution and sets the timer to 1.0. Whether `vt+0xE8` reads this bit is not checked [?].

**0x140D6DCF0 (180 s and 20 s)** = `AlertAiImpl::UpdateReinforce` [dev], not the phase timer and not the 21 s. It runs a separate countdown at state object +0x78, stride 0x30, +0x20, tied to reinforcement: 180 s, or 20 s if the +0x2A count is nonzero; 5 s and 30 s on its other paths.

**Who noticed [D run 1, I names]:** AddNoticeInfo 0x1414DBA80 (self, soldier, info[16]) -> 1 if stored; info[0] = kind. Only soldier 81 noticed: kind 0 from 0x1414E1F27, inside `CheckSightNoticePlayer` (0x1414E0FC0, name from the V_Framework hook list [I]), stored at f5972; alert 251 frames (4.2 s) later. Kind 55 (0x37, from 0x1414DF08C) followed. FoxTrace keeps one row per change, and two alternating kinds give a row each frame (578 rows). Sight scale 100 (`m9_sight100n`): the same pattern, kind 0 at f5890 then kind 55 stored at f6134 and alert at f6135 (245 frames after the sight notice); scale 0 gave no notice row at all (see Capture protocol).

## Radio and member roles [V static, D runs `m9_phase3`, `m9_phase4`, FoxTrace 3.2, soldier 81, CP 39]
Request ids are radio types (`Cp2RadioType` [dev]). A request is a pending entry per CP (impl +0x38, stride 0x18: +0xE handle, +0x12 arg, +0x16 type, priority `GetRadioAttributeByRadioType` 0x140D5B6A0; a new one replaces a pending one only with higher priority) [V 0x140D62660 `RequestRadioByCp`]. Three writers: `RequestRadioByCp` (impl vt+0x30), `Controller_RequestRadioByCp_` 0x140D58050 (vt+0x1D8 of impl-0x18) and `Controller_RequestRadioByMember_` 0x140D58220 (vt+0x1C0) -> `DoRequestRadio` 0x140D5AAA0 [dev names, bodies read]. The radio controller (`RadioControllerImpl`, steps 0x142C3E5B0) posts 0xCE56A00E with the type when it is spoken.

**Member roles:** member record impl +0x50, stride 0x20, +0x1D role, +0x1E counter, payload copied in (`SetMemberRole_` 0x140D63550, impl vt+0x130, the only writer [V]). Roles: 0 none, 1 investigate, 2 radio, 3 guard [names: dev `Cp2MemberRoleCoderImpl::s_processFuncs`]. impl+0x18 (vtable 0x14233F1A0): vt+0x60 0x140D733F0 gives the nearest free member role 2 with a type (the CP's own radios 0x3C, 0x3B are spoken by that soldier, through ByMember_ from 0x141551383); vt+0x58 0x140D73CC0 and vt+0x50 0x140D744E0 give the nearest free members role 1 at the CP's search point (impl +0x80, stride 0x1C).

| Step (both runs, frames) | Run 3 | Run 4 | Source |
|---|---|---|---|
| 0x3C finished; next frame soldier 81 gets role 1 at the search point (-2208.4, 444.1, -1274.4) from vt+0x58 | 12240 -> 12241 | 12153 -> 12154 | [D] |
| `CheckActiveMember` 0x140D69FB0 sets alert record +4 bit 7 while an active member holds role 1; state 2 waits | | | [V] |
| Role 1 cleared by the role update 0x140D7BBE0 (impl+0x18 vt+0x188, call 0x140D7BE72); the same frame state 2 sends 0x3B | **1264 frames (21.07 s)** | **1264** | [D] |
| Evasion entry: soldier 81 gets role 1 again (vt+0x50, call 0x140D744E0) | 13816 | 13731 | [D] |
| The investigator's own step 10 (`InvestigateAiImpl::StepRadio` [dev]; retail table 0x142C5FD10, step 4 empty as in dev) calls the CP's vt+0x1C0 with **literal 0x3A** (0x14149D887) | 17405 | 17318 | [V, D run 4 return address] |
| 0x3A finished (95 frames); next frame evasion -> caution and the role is cleared | 17500 | 17413 | [D] |

So **0x3A = the investigating soldier's report**; evasion lasts as long as the investigation. Pinned in `test_m9_radio.py`. What ends the role: see "Second base" below (0x140D76ED0 = `MemberRoleControllerImpl::DecrementLocatorMember` [dev], called before every clear, not an alternative path [V]).

## Second base: afgh_enemyBase_cp (G5) [V static, D runs `m9_eb1`, `m9_eb2`, FoxTrace 3.3, CP index 18, soldier 6]
Wakh Sind Barracks, lone patrol `sol_enemyBase_0001` (index 6: 24 legs over 34 m, never within 26 m of another soldier of the CP in `m9_village3`). Plan `enemyBase_known` (the `sb_known` steps; the far point is a fixed spot). Both runs clean, baseline MATCH. Pinned in `test_m9_g5.py` (gate M9 G5).

**Search point [V 0x140D7BBE0, 0x140D57260, 0x140D744E0]:** one per CP at impl +0x80 (stride 0x1C, by CP index): +0 position, +0x12 u16 sequence, +0x16 flags (bit 0x40 = current), +0x18. A role-1 order carries the member's link to it (member +0xC u16: bits 7..13 CP index, bits 0..6 sequence). Each new order re-issues the point (sequence + 1, bit 0x40 set). `Controller_CompleteInvestigation_` 0x140D57260 [dev, body read], called by the investigator's AI, clears +0x16 bits 0x40 / 0x80 and +0x18 (and phase record +0x54 bits 15, 16) when the link's sequence is current. The role update 0x140D7BBE0 keeps role 1 for an active member only while the point is current with the member's sequence; otherwise it calls `DecrementLocatorMember` and clears the role (0x140D7BE72). Port: `cp_phase.role_holds`, `complete_investigation`.

**What ends the alert investigate role [D both runs, 7 of 7 role ends]:** the point stops being current (completed), never a re-issued sequence. In alert state 2 the role update drops every holder in the frame the point is completed, `CheckActiveMember` clears record +4 bit 7, and state 2 sends 0x3B **in that same frame** (frames 18526, 15915). The 21 s at sovietBase and the 31 s / 23 s here are the investigators' own walk and search, not a timer.

| Step | `m9_eb1` | `m9_eb2` | Source |
|---|---|---|---|
| Alert entry | 10863 | 9491 | |
| `UpdateFrontLineInAlert` (0x140D661F0 [dev hint], call 0x140D6679E) gives role 1 to **3** members (vt+0x58 count 3) | 11245 (5, 6, 9) | 9672, again 10870 | [D] |
| Front-line roles end through 0x140D66B0B once the point is completed | 14605 | 13287 | [D] |
| Alert state 1 at timer 0, sends 0x3C (vt+0x60, radio member 225) | 16389 | 14267 | [D] |
| 0x3C finished -> state 2; vt+0x58 from 0x140D6D795 gives role 1 to **2** members | 16681 | 14539 | [D] |
| Point completed; role cleared (0x140D7BE72); state 2 sends 0x3B (0x140D6D612), same frame | 18526 | 15915 | [D] |
| 0x3B finished -> evasion; vt+0x50 from 0x140D709DD gives role 1 to **4** members, soldier 6 among them | 18839 | 16199 | [D] |
| 0x51 finished -> 0x53 sent the same frame | 19525 | 16887 | [D] |
| Soldier 6 sends 0x3A (0x14149D887); other investigators' 0x3A came first | 25774 | 20312 | [D] |
| 0x3A finished -> caution next frame, the 4 roles cleared with the point completed | 25953 | 20491 | [D] |

Same in both runs: the phase order, the giver call sites and counts (3, 2, 4), the same-frame 0x3B rule, the radio lengths below. Differs: when the target noticed the player (47 s after the warp in `m9_eb1`), the state 2 wait (1845 / 1376 frames), evasion (7114 / 4292 frames). Evasion timer ran at x0.025 for most of it [D slope], not decoded [?].

**Same rule, other route [D one run, `m9_village1`, afgh_village_cp = CP 3, soldier 118]:** the alert ended at timer 0.30 without 0x3C: the investigator sent 0x3B itself from 0x1413F9324 (a step function with the dev shape of `CombatInDoorImpl::StepRadio` [I, no exact dev map]: op 0 sends 0x3B through vt+0x1C0 when record +0x64 = 1), and the CP's 0x3B callback (timer < 0.8 -> evasion) applied. At evasion entry the old role was cleared because the sequence changed (link 0x181, point sequence 2); at evasion end because bit 0x40 was clear. The alert timer crawled at x0.025 in (0.4, 0.5) **before** record +4 bit 7 was set, so the 10 m test of the slow band passed with the player 490 m away. Its point is the front point of "Alert slow band (G6)": it follows a seen player that is more than 10 m from it, so after the far warp it can sit at the far spot [I: the warp happened while the player still counted as seen (45 frames + 1 s linger); the point itself was not logged in that run]. `m9_eb2` also had soldier 6 send 0x3B from 0x1413F9324 in alert state 0; it had no phase effect there.

## Alert slow band (G6) [V 0x140D65850, 0x140D6B7E0; D runs `m9_g6b`-`m9_g6f`, FoxTrace 3.5, CP index 18]
**The point.** One per CP system, not per CP: impl +0x5D8 (impl vt+0x138 = 0x140D5B3E0 `lea rax,[rcx+0x384]`, +0x254; the phase AI's impl is the `Cp2Operator` sub-object at +0x38 of `CommandPost2Impl`, so it is +0x610 there). Its block S = impl+0x384 also holds CP-wide settings written by the CP SendCommand handler 0x140D5DF30: +0x268 grenade time, +0x27C reinforce time, +0x310 / +0x314 reinforce counts, +0x320 reinforce CP, +0x336 flags [V]. Writer: `UpdateCpAtHost` 0x140D65850 [dev EXACT name for the client twin, AUTO for this one; retail body read = dev body], in alert, every host update:

1. Per player a linger countdown (table +0x218, stride 0x80, +0x54): 1.0 s (0x1420A72CC) while the CP's seen mask has the player, then minus the frame time; the player counts as seen while it is above 0.
2. A seen player's position P (PlayerInfo vt+0x88, or vt+0xB8 under status 0x11) becomes the phase record's last-known position (+0x00), and **the point moves to P when |P - point|² > 100** (0x1420AA7B8); that "moved" flag goes to `UpdateFrontLineInAlert` 0x140D661F0.
So the point is the alert's front line: where the player was seen, re-set only when a seen player is more than 10 m from it. The drain's band test asks whether the player is still within 10 m (and 2 m of height) of that spot.

**Live [D].** FoxTrace 3.5: "cpband" = the alert drain hooked (timer before / after, rate, frame time, record +4, point, last-known position; init row checks the vtable slot), "cpbpt" = the point polled every frame.

| | `m9_g6b`, `m9_g6c` (enemyBase_known) | `m9_g6d` | `m9_g6e` | `m9_g6f` |
|---|---|---|---|---|
| Point written (= alert entry frame, the player's spot) | 10882, 12174 [I: from the first drain row; no per-frame poll yet] | 11902 | 10685 | 10079 |
| Point rewritten later | never (player pushed < 10 m) | never | never | never |
| Band on (timer 0.4995, x0.01) | never: seen until the far warp | yes, record +4 bit 7 clear | yes, bit 7 also set | yes, bit 7 clear |
| After the far warp | x1 through 0.5..0.4 | x1 | x1 | x1 |

The last three use plan `enemyBase_band`. In all three the player was seen again 21 to 63 s after the band started (frames 15603, 13702, 14745) (sight scale 0 does not block every report at close range [?]), which reset the timer to 1.0. So the 10 m test alone switches the band on in two runs, and the point never moves while the player stays within 10 m, while the last-known position follows the player (pushes up to ~6 m). `enemyBase_band` = `enemyBase_known` with IH sight / hearing scale 0 once alert is reached, so the player stays unseen at the alert spot for 75 s before the far warp (IH settings are not saved: the run writes no save, `ih_save.lua` unchanged). Every logged drain update equals `alert_drain_step` bit-exact. Port: `cp_phase.front_point_update`, `linger`, `near_point`, `alert_drain_step`; test `test_m9_g6.py` (gate M9 G6).

## Radio lengths [V 0x140DA1CE0, D 7 runs]
`RadioControllerImpl` (steps at 0x142C3E5B0 by record +0xB; Update 0x140DA24F0 [dev]) per CP: `StepIdle` 0x140DA1C70 moves to `StepRadio` 0x140DA1CE0 once the CP's pending entry has a handle; `StepRadio` hands the entry to the CP's voice player (impl+0x10 vt+0) and waits on the player's two state bytes per CP: bit 4 -> chaff step, bit 2 -> drop without a finish, bit 1 -> no-response step (sends 0x4B), else when the busy byte is 0 (or a Quark query 8 answers true) it posts 0xCE56A00E with the type. **So a radio lasts as long as its voice line plays** (sound data, M12 / M21), not a code table. Write (DoRequestRadio) -> finish, frames:

| Type | sovietBase 3, 4 | village 1 | enemyBase 1, 2 | Speaker |
|---|---|---|---|---|
| 0x3C | 147, 147 | not sent | 147, 147 | radio member |
| 0x3B | 145, 147 | 162 | 147, 147 | radio member (village: investigator) |
| 0x3A | 95, 95 | 162 | 178, 178 | investigator |
| 0x51 | 685, 689 | 687 | 686, 688 | CP (no member write) |
| 0x53 | 611, 624 | 622 | 621, 623 | CP |
| 0x3D (from the CP send) | 421, 403 | 378 | 393, 377 | CP |
| 0x1C (caution, repeats every ~12.4 s) | | 64 | 63, 64 | member |

A CP send to the member's write adds 110 to 165 frames (the member is chosen and reaches `StepRadio`). Tool `Tools/m9_radio_lengths.py`.

## Phases [D, forced, soldier 78, afgh_sovietBase_cp, player 120 m away]
- Sneak: route 1E072FB4, state 2 at the node.
- SetPhase caution: route changes at once to F49C0789, state 0, bits 0x04 then 0x14 then 0x24: stands, walks, runs to the new route. Same in both runs. State 2 on arrival.
- Commanded evasion falls back to caution by itself after about 26 s (both runs); state 3 then 0 or 1, moving again.
- Alert: state 3, dash and stops (bits 0x40, 0x04, 0x00). In forced1 commanded sneak after alert brought the sneak route 1E072FB4 back at once, `IsOnRoute` true in the same second, and the soldier stayed at state 2 where it stood, about 110 m from that route, for the remaining 90 s. Not repeated [?].
- Evasion and alert differ between runs after the first steps, so only the part above is pinned. Without a known target the alert is not a fight.

Forced2 ended at 244 s (reply lost on the pipe, driver now retries and always writes its result), so "after alert" has one run.

Seen in hand play only, not pinned: other CPs went to caution when this CP fell back (`m9_humanplay1_contaminated`) [?].

## Extension points
Mod API: [`docs\engine\ModAPI.md`](mod-api.md). Built (M10 G1): phase rates, realize margins and route constants are `parameters`, the route step table, request ids and investigator counts are `ai_tables`, all registered by vanilla. Built (M10 G3): hook sites `route.switch` (`route_follow.step_after`) and `cp.phase_change` (`cp_phase.phase_change`), table inserts (`ainode` reference mod), rate override (`alertrate`). Planned overrides and hooks:

- **Radio types and priorities:** the per-type attribute (`GetRadioAttributeByRadioType`) and what each type's finish does (the per-phase callbacks) as a registry; a mod adds a type or changes which finish ends a phase.
- **Member roles:** role kinds (none, investigate, radio, guard, mortar, turret, anti-sniper ...) registered with their process step, so a mod adds a role or changes how many members investigate (live: 3 at the alert front line, 2 in alert state 2, 4 in evasion; `cp_phase.INVESTIGATORS`).
- **Search point and completion:** the per-CP search point and the completion rule (`role_holds`, `complete_investigation`) as hooks, so a mod ends or extends an investigation.
- **Radio lengths:** a radio lasts as long as its voice line; the engine takes the length per type and voice as data (measured table above) until audio (M21) plays it.
- **Front point and slow band:** the 10 m front-line radius, the linger time and the band edges / multipliers (`cp_phase.front_point_update`, `alert_drain_step`) as per-CP settings, so a mod widens or disables the alert's slow fade.
- **Phase rates and multipliers:** the per-CP rate block (impl +0x28) and the drain multipliers, overridable per CP (what the retired V_Framework `SetCautionPhaseDuration` did by hooking).
- **Unrealized speeds:** the (phase, speed, flag) table and crouch scale as data.
- **Realize budget and window inset** (18 soldiers, 32 / 28 m) as settings.

## Evidence
- Verifiers: `test_m9_soldier.py`, `test_m9_route.py`, `test_m9_phase.py`, `test_m9_radio.py`, `test_m9_g4.py`, `test_m9_g5.py`, `test_m9_g6.py` (fixtures `m9_*.json`).
- Live runs: `Memory\research\m9_*_<timestamp>\` (route, known target, phase, radio, enemyBase, G4 and G6 runs named in the sections above) and `m8_nav14` / `m8_nav15`.

## Open
- G6 leftovers (not gate items): why the seen player's position stayed at the pre-warp spot for 81 frames after the warp in `m9_g6b`, `m9_g6d` (PlayerInfo vt+0x88 vs vt+0xB8 under status 0x11), so the village case is [I]; the 0.25 timer floor in alert while a member byte has 0x40 (0x140D65850); what (impl+0x18) vt+0xA8 counts (x0.025 at the village, x0.01 at enemyBase).
- Which flag-word bits give the unrealized (phase, speed) pair (task +0xC2 not logged live); crouch case.
- Phase lengths: request rule, investigate role, 0x3A report, role end (point completed) and radio lengths pinned (`test_m9_phase.py`, `test_m9_radio.py`, `test_m9_g5.py`); the slow band's 10 m point (impl +0x5D8) is written by `UpdateCpAtHost` 0x140D65850 (G6, "Alert slow band (G6)"); still open: the evasion x0.025 stretch at enemyBase, how long an investigator searches before `CompleteInvestigation`, commanded evasion's 26 s, whether `SetKeepCaution` feeds `vt+0xE8`, the 0x1413F9280 step's class.
- Route following leftovers (not gate items): vehicle arrival test 0x14156CF30, steps 6-0xF and 0x11, the single-action selector (impl +0x158) and its animation lengths (M16), the random source of the act interval, what the conversation notice (kind 60) starts.
- Sight scale runs repeated once more each; hearing, which needs a noise source; the hit-push path of the driver.
- Africa (afgh second base done: G5); the +0x1A0 byte (0 on all soldiers in the last 20 samples of `m9_route1`), the view test and the slot swaps in the port.

---
<small>Source: `docs/engine/SoldierAI.md` in the project repository &middot; generated 2026-11-05.</small>
