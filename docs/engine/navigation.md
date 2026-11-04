# Navigation and routes

Status: **PASS for paths (Luc, 2026-11-01); route following near the player moved to M9.** `Engine\world\navigation.py` equals the game on 948 of 948 live jobs (x/z within 0.1 m, afgh free roam, sneak phase, player far from soldiers). Edge event -> speed class is decoded and far route following is checked; the state sequence near the player is M9 work. Format: [`docs\NAVMESH.md`](../formats/nav2.md), [`docs\formats\FRT.md`](../formats/frt.md). Verifier: `Engine\tests\test_m8_nav.py`, fixtures `m8_nav_jobs.json` (`Tools\m8_nav_jobs_fixture.py`) and, as a regression floor, `m8_nav_paths.json` (`Tools\m8_nav_fixture.py`, run `Memory\research\m8_nav_20261029_185330`).

## Pipeline [V static]
Goal → `TppNavigationController_RequestMove` 0x140FA2430 (vtable 0x1423A1610 slot 0; `self, slot, req`) → snap (slot +0x48, 0x140FA1E30 → Navx system at Quark table +0xA0, vt +0x20) → `PathPlanner_StartPath` 0x141CC7500 (planner vtable 0x142516090) → start not on the navmesh: `PathPlanner_DirectPath` 0x141CC79A0 (one straight waypoint); on it: `PathPlanner_QueueNavmeshPath` 0x141CC75E0 (async job, lock 0x142C85048). The job is decoded below ("Path job").

## Path job (2026-10-31) [V static unless tagged]
`QueueNavmeshPath` queues six stages on `PathfindDaemon` (global 0x142C84B38, runner 0x141CC8D70; stage vtable: +8 begin, +0x10 update, +0x18 end; update returning 3 skips ahead to the post-process):

| Stage | Update | Does |
|---|---|---|
| 1 | 0x141CB7AD0 | Snap start and goal, list their triangles' edge nodes as seeds and goals |
| 2 | 0x141CBFF50 -> 0x141CC0120 | Only if start-goal distance² < 6400: plain A*, cap 512 nodes; success skips to stage 6 |
| 3 | 0x141CB7DE0 -> 0x141CCE3F0 | Cluster A* over the tail graphs ([`docs\NAVMESH.md`](../formats/nav2.md)); limits stage 4 |
| 4 | 0x141CBEE20 -> 0x141CBF110 -> 0x141CB9780 | Region A* inside those clusters; builds a corridor of up to 64 regions, 448 region nodes, then a nearer h target in the work area (+0x30); Q +0x30 stays the goal |
| 5 | 0x141CBFB00 -> 0x141CBFCB0 | A* restricted to the corridor |
| 6 | 0x141CC0470 -> 0x141CC0710 | Runs the navigator's post-process list |

**A\*** (0x141CB83E0): open heap on f = g + h (exact sift rules 0x141CCE210, 0x141CBF5A0, 0x141CBEC90). h = 3-D distance to the goal × m, stored once per node. g = trunc((g + link weight / header+0x4A × m) × 100 + 0.5) × 0.01. m = query cost multiplier if region attribute & cost mask, else 1. Twin and tile links cost 0. Ends when a goal node is popped.

**Post-process** (list by navigator name, 0x141C92DB0; soldiers: GeneralNavigatorWithExtender = A, B, C, extender [D: live 4 m points]). This answers why corners are neither vertices nor nodes:

- A 0x141CC0B10: node positions, dropping points within 1e-8 m², then the goal.
- B 0x141CC4230: up to 10 Gauss-Seidel passes; each point moves to where the line previous -> next crosses its node's triangle edge, the edge shortened 2 cm at each end (0x141CC3D70), clamped. Nodes of kind != 0 stay fixed. So corners sit partway along edges.
- C 0x141CC1590: first tries a ray start -> goal. Otherwise walks the points from an anchor; when the ray to point i fails it emits point i - 1 as a corner and the next test goes to i + 1.

- Extender 0x141CC2560: pass 1 replaces a run of segments under 4 m by the crossing of the extended incoming and outgoing lines (each extended 4 m, crossing test 0x141CC9710 with 1e-4 slack), pushed out 0.05 m along both directions (0x1421C0120); triangles of new points are looked up at point + world +0x20 (0.1 live) with filter 0xFFFF; pass 2 stretches a segment under 4 m into a point to exactly 4 m along its direction, if the new point is not past the next. Both need rays to and from the new point to pass. This is the "first corner exactly 4 m from the start".

**End state** 0x141C854A0: Q +0xB8 (kept) comes from stage 3 ((result == 1), or result 1 / 3 with an unloaded goal); from stage 4 only if no cluster graph applies. Q +0x11B (reached) from stage 5. The goal is a path point only if both are set. A stopped search whose region chain holds at most 512 nodes (0x141C7CD50) counts as reached without the goal; then the last point relaxes towards its own node, so it stays there (0x141C86C80). This was the 0.11 m miss.

**Stage 3 limits** 0x141CB7DE0: clusters from the start side, at most 8 tiles and 32 clusters. The cluster where that runs out becomes the h target and its representative node (tail block +8, u64 per cluster, 0x141CA9740) a further goal (0x141CB8210); +0x410 then keeps stages 4, 5 from using the boundary rule and from reaching.

**Region links:** a reverse link's back index counts inside its own list, same mesh or other piece (0x141CB9780). Reading it as one index over all lists gave wrong costs and the wrong long routes.

**Ray** 0x141C9FC90 walks triangles in x/z, leaving through the edge the line crosses, following link words ([`docs\NAVMESH.md`](../formats/nav2.md)); a wall ends it unless the end point lies on that triangle. A missing start or end triangle is looked up by position (0x141C9FAE0), so runtime nodes get one. It counts flagged triangles (per-tile bits +0x38 +8); only if it met any does it test the segment against the active obstacle boxes (0x141CB2A40, 0x141CB30D0: unit box after position, rotation, size).

**Query values [D live]:** radius self +0x5C = 2.0 on all jobs; filter from req +0x80, else per-slot default (*(self+0x60) + slot*2): 0x201 usual, 0x211, 0x1; cost mult req +0x84, cost mask req +0x82 (mult 2, mask 8 on 190 of 4,195 jobs). Snap considers only regions whose box contains the point lifted 0.5 m (x, z inside; ymin <= y; y - radius <= ymax in quanta, 0x141C9F780).

**Re-requests** (`RequestMove` running-path branch): the new query starts at a sub-goal req +0x88 (5 m) along the old path, with mult 1 and mask 0; the old prefix stays in the path. So the first path point is not the query start. **Two-waypoint requests also start hidden next-leg jobs** that `RequestMove` never sees.

## Streaming decides paths [V static + D live]
`PathPlanner_StartPath` tests the point against **loaded** nav blocks only (0x141C85400; world +0x290 / +0x298, block +0x4C = T << 15 | part, part 1 = `.1` file). Outside them: `DirectPath`, one straight line. 16-26 blocks were loaded at a time, changing with the player. Live: 3,865 of 4,162 finished jobs (93 %) in the clean capture were direct. So far-away soldiers walk straight lines, and a path query needs the loaded-block set as input.

## Runtime state a job depends on [V static + D live]
A path depends on the moment, not only on the map. The fixture records all of this per job, like the loaded blocks; nothing in the engine creates it yet.

- **Block bits**, set bit = blocked: triangles [7] +8, nodes [8] +0x28, links [8] +0x30, regions [9] +0x50 (none set in any capture). They appear where vehicles stand and toggle during a run: 0x141CB83E0 skips blocked links, 0x141CA4EF0 skips blocked nodes.
- **Obstacles** ("bounders"), world +0x350 / +0x358: +0x10 size, +0x20 rotation, +0x30 position, +0x7C bit 1 active, +0xA4 first ring node, +0xAA ring node count.
- **Runtime meshes:** two pools made by 0x141C888B0 with the file meshes' layout but float vec4 nodes. Id 0x40000000 (T 0x8000): obstacle rings, 4 nodes kind 2 per region, placed around the box when active. Id 0x40008000 (T 0x8001): off-mesh links, 2 nodes kind 1 per region, e.g. (530.0, 320.2, 1151.7) -> (529.5, 324.0, 1150.2). Unused nodes have their block bit set.
- **Dynamic link lists:** world +0x90 (node level, 12-byte entries: u32 id, u16 record, u16 region, u16 node, u16 flags), +0x110 (region level, 20-byte entries, layout under "Region links" below), +0x130 (portal node lists), +0xB0 (records, stride 0x18: +0x10 u16 cost, +0x12 flags; +0x18 valid bits). Piece [8] +0x58 and [9] +0x28 are packed 12-bit tables, node or region -> list index, 0xFFF = none. Written by 0x141C7CE30, removed by 0x141C7DF60 / 0x141C7E800.
- **Node search** 0x141CB83E0: after the in-mesh links, each entry of the node's list: in the corridor if the search has one and entry flag bit 0 is set, region filter, record valid and flag bit 0, cost = record cost / 256 added without rounding.
- **Region search** 0x141CB9780: after the file links, each entry of the region's list: cluster check if flag bit 2, cost = entry cost / 256 if flag bit 0, plus the reverse entry's (index +0x11) cost, h at multiplier 1, no rounding. Entry: u32 id, u16 region +4, u32 far id +8, u16 point list +0xC, u16 cost +0xE, flags +0x10, back index +0x11. First expansion and goal regions use real searches, as for file links.
- **Blocked region link pairs**, piece [9] +0x40 / +0x48: key (T << 15 | piece) << 32 | region << 16 | entry link << 8 | exit link, tested on every expansion but the first. Removed with the dynamic links (0x141C7E360). Live they sit on tiles 2083, 2660, 2662, on regions with dynamic links; links past the file count are the dynamic ones. They forbid mixing a file link with a dynamic one in the same pass [I]. Who adds them is not found [?]. The entry index of a tile link is its index in the far region's third list, or 0xFFFF; the port stores 0xFFFF only, no live job depends on it.
- **Seeds and goals** 0x141C84C80: free edge nodes of the triangle. On a flagged triangle, obstacles over it (0x141CB0AA0, at most 30) hide nodes whose line from the point crosses their box, and add those ring nodes a ray from the point reaches, at most 16 in all. A goal inside a box therefore has no goal nodes.

**Names [W, I]:** the community wiki's `NavWorld` properties `navigationGraphDynamicLinkContainerInfo`, `segmentGraphDynamicLinkContainerInfo`, `islandGraphDynamicLinkContainerInfo`, `maxGraphBounderCount`, `maxTacticalActionCount` fit node search / region search / cluster stage, the dynamic lists and the obstacles. `GkTacticalAction` (`Door`, `LadderUp`, `LadderDown`) has fox2 entities only in mtbs; afgh has `TppLadderData` in 34 files, not yet matched to these links. Not checked in the exe.

## Capture method and conditions
FoxTrace `navreq` hooks `StartPath` and logs one `navjob` per job (exact input, own output, direct flag). **Three traps, all found by jobs that looked wrong:**

- Q +0x134 (state) is set by stage 5, but the post-process list can run over several frames. The job is finished at Q +0xB9 (0x141CC0812), or at once for direct paths. Earlier captures read the path at state >= 2, so long jobs held unfinished raw node lists: the 11 "long route" misses of `m8_nav6` / `m8_nav7` were this plus the back-index bug. **Captures before `m8_nav10` cannot be used for paths.**
- Loaded blocks, bits and obstacles must be read at job start. Read at job end they lag by a frame or more: jobs right after a streaming change looked "unloaded" (`m8_nav13`, 2 of 485).
- `navbits` is opt-in and bounded (triangles exact, 3 links per triangle): the tables are read by count, memory past them is junk that spammed 270 MB in `m8_nav9`.
**Do not use `navpath` to pair input and output**: it can read the previous path or a later leg's input.
Conditions matter (Luc, 2026-10-31): captures record player position, phase and life (`Memory\research\m8_nav2_20261030\drive2.py`) and stay away from soldiers. `m8_nav2` / `m8_nav3` are contaminated. Capture 9's boot failure ("game window not found") was Windows powering off (System log event 1074 at 11:48:43), not the game or FoxTrace. A sneak-vs-alert comparison is still untested.

## Accuracy against live jobs (2026-11-01)
`Engine\world\navigation.py` ports all six stages, runtime blocks, runtime meshes and dynamic links. Fixture `m8_nav_jobs.json` (runs `m8_nav14_20261101_180029`, `m8_nav15_20261101_181436`, FoxTrace `33B4F265`, no `ChangePhase` or `PlayerDamaged` in either): every job gets its recorded start, goal, filter, cost, loaded blocks and runtime state.
**948 of 948 jobs within 0.1 m: 639 searched (25 coarse), 309 direct.** Also, with earlier builds of the port's inputs: `m8_nav12` 472 of 472, `m8_nav13` 483 of 485 (the two start-frame jobs above). `m8_nav14` was first run after the last code change and matched without further fixes, so it is a held-out check; `m8_nav15` is the second clean run. All captures use the same warp route in f30010 and the sneak phase, so this says nothing yet about alert, other missions, mafr or mtbs.
What made it equal, in order of effect: x/z scale, loaded blocks, extender step (863 of 883 on the old fixture); then reverse-link cost, logger fix, seeds and runtime meshes, end state, extender push.

## Route following [D live]
With the player far away, soldiers move exactly on `.frt` route edges: of 170 moving soldiers, 97 stay within 5 cm of one f30010 route for all 90 s and advance in node order; speed 0.80 m/s on every walk event seen (`RelaxedWalk`, `RelaxedWalkAct`, `RelaxedStandWalkAct`, `CautionWalk`, `CautionWalkSearch`, 0x4E87F5A9), so far soldiers do not use it for speed differences within walk. **Far mode = the unrealized state, picked each frame by a budget inside the stage window, not a distance; realized soldiers walk at 0.975 m/s and stay within 2 m of the edge (99 %) [V + D, `SoldierAI.md`].** The 18 m stray of runs B, C of `m8_nav_20261029_185330` was uncontrolled and did not come back in clean runs.

**Edge event -> speed class [V 0x140ED4C10]:** 1 walk by default; 2 run: `RelaxedRun`, `CautionRun`, `CautionRunAim`, 0x62FE8037; 3 dash: `CautionDash`. Move family [V 0x140ED1FE0]: caution 0x62FE8037, 0x0AF9CFF0, `CautionRun`, `CautionWalk`, `CautionWalkAim`, `CautionRunAim`; relaxed `RelaxedWalkAct`, `RelaxedWalk`, `RelaxedRun`, `CautionDash`. Run and dash speeds [D]: realized 2.50 / 4.01 caution run, dash 6.43; unrealized 2.00 / 2.75, dash 4.00 (`SoldierAI.md`). The other 73 do not fit a single route at that tolerance: an offset of about 1 m on pairs was seen, vehicle riders go faster, route changes were not separated [?].

`GetUsingRoute` / `GetDoingRouteEventIndex` exist only on the heli handler [V], hence nil for soldiers. The soldier's route and route state are table fields (impl +0xE8, `SoldierAI.md` "Route state"); FoxTrace `soldier` logs them. Routes in the M8 fixture stay identified by geometry.

## Engine module (`Engine\world\navigation.py`)
`NavWorld.add_file`, `set_loaded`, `set_blocked`, `set_runtime`, `in_loaded`, `locate`, `find_path(start, goal, filter=, cost_mult=, cost_mask=)` (sets `status`), `subgoal_along`, `track_route`, `edge_speed_class`, `edge_move_family`. Vertices, node positions, g / h / f and relaxed points are float32; the ray's side tests compare float32 inputs in double [I: no difference at the gate margin, revisit for C++]. The obstacle / triangle overlap test is a separating-axis version of 0x1401A73F0 [I].

## Extension points
Mod API: [`docs\engine\ModAPI.md`](mod-api.md).

- **Nav worlds and path queries**: a mod world brings its own `.nav2` (MOD-D); the codec is the registered loader for `nav2` / `1.nav2` [B M10 G1].
- Route step table and arrival distances are registry data (`ai_tables` `route.*`, `parameters` `route.*`) [B M10 G1]; overriding them is MOD-B / M10 G3.

## Evidence
- Verifiers: `test_m8_nav.py` (fixtures `m8_nav_jobs.json`, `m8_nav_paths.json`), `test_nav2_roundtrip.py`, `test_nav2_all.py` (format, slow).
- Live runs: `Memory\research\m8_nav*_<timestamp>\` (FoxTrace nav captures, runs named in the sections above).

## Open (E33)
What creates the runtime state: block bits and obstacle activation, ring placement, off-mesh link sources (0x140502FC0 -> 0x141C7CE30), who adds blocked pairs; the engine replays them. Cluster-level dynamic links (`islandGraph...`) are not ported and no job needed them. Sneak-vs-alert comparison on the same jobs; other missions and locations; what starts a path request while on a route (`SoldierAI.md`, open).

---
<small>Source: `docs/engine/Navigation.md` in the project repository &middot; generated 2026-11-05.</small>
