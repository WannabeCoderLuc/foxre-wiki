# Navigation and routes

Status: **IN PROGRESS, gate open.** `Engine\world\navigation.py` equals the game on 863 of 883 live jobs; the 20 misses are all coarse-search jobs. Format: [`docs\NAVMESH.md`](../formats/nav2.md), [`docs\formats\FRT.md`](../formats/frt.md). Verifier: `Engine\tests\test_m8_nav.py`, fixtures `m8_nav_jobs.json` (`Tools\m8_nav_jobs_fixture.py`) and, as a regression floor, `m8_nav_paths.json` (`Tools\m8_nav_fixture.py`, run `Memory\research\m8_nav_20261029_185330`).

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

- Extender 0x141CC2560: pass 1 replaces a run of segments under 4 m by the crossing of the extended incoming and outgoing lines (each extended 4 m); pass 2 stretches a segment under 4 m into a point to exactly 4 m along its direction, if the new point is not past the next. Both need rays to and from the new point to pass. This is the "first corner exactly 4 m from the start".

**Ray** 0x141C9FC90 walks triangles in x/z, leaving through the edge the line crosses, following link words ([`docs\NAVMESH.md`](../formats/nav2.md)); a wall ends it unless the end point lies on that triangle; start-triangle-less rays fail. It also counts triangles flagged in a per-tile bit table (+0x38 +8) and then checks 0x141CB2A40.

**Query values [D live]:** radius self +0x5C = 2.0 on all jobs; filter from req +0x80, else per-slot default (*(self+0x60) + slot*2): 0x201 usual, 0x211, 0x1; cost mult req +0x84, cost mask req +0x82 (mult 2, mask 8 on 190 of 4,195 jobs). Snap considers only regions whose box contains the point lifted 0.5 m (x, z inside; ymin <= y; y - radius <= ymax in quanta, 0x141C9F780).

**Re-requests** (`RequestMove` running-path branch): the new query starts at a sub-goal req +0x88 (5 m) along the old path, with mult 1 and mask 0; the old prefix stays in the path. So the first path point is not the query start. **Two-waypoint requests also start hidden next-leg jobs** that `RequestMove` never sees.

## Streaming decides paths [V static + D live]
`PathPlanner_StartPath` tests the point against **loaded** nav blocks only (0x141C85400; world +0x290 / +0x298, block +0x4C = T << 15 | part, part 1 = `.1` file). Outside them: `DirectPath`, one straight line. 16-26 blocks were loaded at a time, changing with the player. Live: 3,865 of 4,162 finished jobs (93 %) in the clean capture were direct. So far-away soldiers walk straight lines, and a path query needs the loaded-block set as input.

## Capture method and conditions
FoxTrace `navreq` now hooks `StartPath` and logs one `navjob` per job (exact input, own output, direct flag), plus `navtiles` on each loaded-set change. **Do not use `navpath` to pair input and output**: it can read the previous path or a later leg's input.
Conditions matter (Luc, 2026-10-31): captures must record player position, phase and life (`Memory\research\m8_nav2_20261030\drive2.py`) and stay away from soldiers. `m8_nav2` / `m8_nav3` had 50 / 30 `ChangePhase`, 4 / 19 `PlayerDamaged`, 1 / 8 deaths by the player and are contaminated (`m8_nav3` also has manual weapon, crawl and binocular inputs). `vars.playerPhase` alone is not enough: it stayed 0 while command posts went to caution after a soldier-vehicle accident.
Clean run: `Memory\research\m8_nav6_20261031_001648` (warps 100+ m from every soldier position seen earlier, no input). It has only 299 non-direct jobs, 39 of them multi-point, so it is thin on real searches; it is not a sneak-vs-alert comparison either, which is still untested.

## Accuracy against live jobs (2026-10-31)
`Engine\world\navigation.py` ports all six stages, without the runtime block lists and off-mesh links below. Fixture `m8_nav_jobs.json` (`Tools\m8_nav_jobs_fixture.py`, clean runs `m8_nav6`, `m8_nav7`): every job gets its recorded start, goal, filter, cost and loaded blocks.
**Overall 863 of 883 jobs within 0.1 m (2026-11-01): plain search finishes 530 of 530, outside loaded blocks 324 of 324, coarse 9 of 29.** The gate stays a strict xfail. The fixture holds the same jobs from two runs, so the 20 misses are about half duplicates.
What made it equal, in order of effect: the x/z scale ([`docs\NAVMESH.md`](../formats/nav2.md) "Quantisation"), the loaded blocks, the extender step.
**Earlier theory rejected:** the corners near goals were not dynamic obstacles. Live there are only 4 entries in the obstacle list (world +0x350), 2 with real boxes, none near those corners; they came from the wrong scale. Obstacles remain unported and untested.

**Still wrong: 20 coarse jobs.** Search result 3 = reached the loaded boundary, keeps the goal as last point; result 2 = cap reached, best-h node, no goal (0x141C854A0).

| Jobs | Deviation | Note |
|---|---|---|
| m8_nav6 1903, 1904, 1913, 2521, 2522, 2782, 2791; m8_nav7 1893, 1905, 2507, 2508 | 17.7-64.2 m | Long routes, different region path |
| m8_nav6 800, 826, 2824; m8_nav7 815, 2829 | 2.7-2.8 m | Off-mesh link jobs [D] |
| m8_nav6 2560, 2638; m8_nav7 2565, 2633 | 0.11 m | Just over the margin, cause not looked at |

On the long routes my region route costs less than the game's under the stored link costs (job 1905: 225.9 against 239.4 at the same region; job 2507: 410.2 against 413.1), and the live clusters lie inside my cluster path. So the game either cannot use my route or orders its pops differently. The live region list is derived from stage 5's node path, so this is indirect [I].

**Runtime state the region search reads and the port lacks [V static 0x141CB9780, contents not captured]:**

- Blocked region link pairs: piece qword [9] +0x40 count, +0x48 u64 list. Key = node id (T << 15 | piece) << 32 | region << 16 | entry link << 8 | exit link. Tested on every expansion but the first; a match skips the link. So one way through a region can be forbidden without disabling the region. 0x141C7E3BA removes both orders of each pair; the code that adds them is not found.
- Region bits: [9] +0x50, set bit = blocked, tested with the region filter.
- Off-mesh links in the region graph: [9] +0x28 is a packed 12-bit table by region (0xFFF = none) into a list at search param [3] +8 (stride 0x10: pointer, u16 count). Entries are 20 bytes: u32 node id, u16 region at +4, list index at +0xC, u16 cost at +0xE, flags at +0x10 (&1, &4 = cluster check), byte at +0x11.

**Set bit = blocked** [V 0x141CB83E0: link bits [8] +0x30; 0x141CA4EF0: node bits [8] +0x28].

**Live bits, partial** (`m8_nav8_20261031_114257`): the logger read past the tables and hit its size cap, so 522 of 538 records fully cover one tile, 0x8A6. Filtered to each mesh's counts, the only set bits are on 0xA66: piece 1 triangles 24, 25 and nodes 59, 61; piece 4 triangles 1043-1045. No link or region bits on the logged tiles. World +0x20 = 0.1 and class table +0x78 = 00020100 00000000 03000001 03030303 as logged, bytes not yet interpreted. This does not settle the long routes.
**Capture 9 has no data** (`m8_nav9_20261031_114822`): the boot failed ("game window not found"), cause not established. The FoxTrace build from it, one `navbits` line per piece plus the pair list, has never logged in game.

## Route following [D live]
With the player far away, soldiers move exactly on `.frt` route edges: of 170 moving soldiers, 97 stay within 5 cm of one f30010 route for all 90 s and advance in node order; speed 0.80 m/s at the median over all route types seen. The other 73 do not fit a single route at that tolerance: an offset of about 1 m on pairs was seen, vehicle riders go faster, route changes were not separated [?]. Near the player, soldiers also leave routes (up to 18 m) and stay on the navmesh. Which edge events set which speed, and the state sequence near the player, are not decoded.

`GetUsingRoute` / `GetDoingRouteEventIndex` returned nil for TppSoldier2 instances through `GameObject.SendCommand`, so routes in the fixture are identified by geometry.

## Engine module (`Engine\world\navigation.py`)
`NavWorld.add_file`, `set_loaded`, `in_loaded`, `locate`, `find_path(start, goal, filter=, cost_mult=, cost_mask=)` (sets `status`), `subgoal_along`, `track_route`. Vertices, node positions, g / h / f and relaxed points are float32; the ray's side tests compare float32 inputs in double [I: no difference at the gate margin, revisit for C++]. Extender tri lookup lift 2.0 = world +0x20 [I]; capture 8 logged world +0x20 = 0x3DCCCCCD (0.1), so this needs rechecking.

## Open (E33)
Blocked pair list and region bits live, and who writes them (the gate needs them); off-mesh links in the region graph and node search; the 0.11 m misses; dynamic obstacles (source, effect on link and triangle bits, their runtime meshes); sneak-vs-alert comparison on the same jobs; where off-mesh links come from (a soldier climbs ~4 m at one spot at (-513, 325-328, 548), ladder or stairs [I]); `.frt` edge events → speed; route selection near the player.

---
<small>Source: `docs/engine/Navigation.md` in the project repository &middot; generated 2026-11-01.</small>
