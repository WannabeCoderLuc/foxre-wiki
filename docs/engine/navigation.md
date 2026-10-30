# Navigation and routes

Status: **IN PROGRESS, gate open.** `Engine\world\navigation.py` approximates the game's paths; it does not equal them yet. Format: [`docs\NAVMESH.md`](../formats/nav2.md), [`docs\formats\FRT.md`](../formats/frt.md). Verifier: `Engine\tests\test_m8_nav.py`, fixture `m8_nav_paths.json` (`Tools\m8_nav_fixture.py`), run `Memory\research\m8_nav_20261029_185330`.

## Pipeline [V static]
Goal → `TppNavigationController_RequestMove` 0x140FA2430 (vtable 0x1423A1610 slot 0; `self, slot, req`) → snap (slot +0x48, 0x140FA1E30 → Navx system at Quark table +0xA0, vt +0x20) → `PathPlanner_StartPath` 0x141CC7500 (planner vtable 0x142516090) → start not on the navmesh: `PathPlanner_DirectPath` 0x141CC79A0 (one straight waypoint); on it: `PathPlanner_QueueNavmeshPath` 0x141CC75E0 (async job, lock 0x142C85048). The search and smoothing inside that job are **not decoded** [?].

## Request record (`req`) [V static + D live, 1,895 requests]
| Off | Field |
|---|---|
| +0x00 | start vec4 |
| +0x10 | goal vec4, w = 1 |
| +0x20 | second waypoint vec4 (0 when count = 1) |
| +0x70 | owner hash (48 bit); 4 distinct values in the run, one for 1,889 requests [?] |
| +0x78 | waypoint count: 1 or 2 |
| +0x84, +0x88, +0x8C | float: 1 or 2; 5 (rarely 1); 10 (rarely 1) [?] |

Planner slot: `*(self+0x30)+8 + slot*0x10`: +0 path object, +9 status (3 or 5 = path readable), +10 flags. Path object: +8 points (vec4 stride 0x10), +0x20 count [V static `GetPathPoint` 0x140FA1A90]. In the run the status was 3 on every finished path.

## What the live paths show [D]
FoxTrace directive `navreq` logs each request and its finished path (reads only). One run, f30010, ~8 min, two camps: 1,895 requests, 1,891 finished paths, 134 soldier slots.

- **Far soldiers request paths too**, and most are short: route following asks for the next node(s). Median path 3.8 m, longest in the compared set 90 m; 2 to 5 points in almost all, up to 9.
- 420 single-waypoint and 1,154 two-waypoint requests start a fresh path; 317 extend a running path (the first path point is not the request start). The path ends at +0x10.
- Path corners lie on **mesh types 4 and 5** only (400 sampled corners; types 0-3 are 50-80 m away). `afgh_common_nav.fox2` defines the agent classes Human (r 0.4), Vehicle (r 3.5), Middle (r 4), HumanHighCost (r 0.4) and a fifth entry; which class is which type number is [?].
- Path corners are **neither mesh vertices nor portal nodes** (nearest vertex 2.5 m, nearest node 1.3 m at the median, type 4); some interior points are collinear with their neighbours. So the game's smoother is not plain string pulling over mesh vertices [I].

## Route following [D live]
With the player far away, soldiers move exactly on `.frt` route edges: of 170 moving soldiers, 97 stay within 5 cm of one f30010 route for all 90 s and advance in node order; speed 0.80 m/s at the median over all route types seen. The other 73 do not fit a single route at that tolerance: an offset of about 1 m on pairs was seen, vehicle riders go faster, route changes were not separated [?]. Near the player, soldiers also leave routes (up to 18 m) and stay on the navmesh. Which edge events set which speed, and the state sequence near the player, are not decoded.

`GetUsingRoute` / `GetDoingRouteEventIndex` returned nil for TppSoldier2 instances through `GameObject.SendCommand`, so routes in the fixture are identified by geometry.

## Engine module (`Engine\world\navigation.py`)
`NavWorld.from_nav2(files, classes=(4, 5))`, `locate`, `snap`, `find_path`, `track_route`; float32 buffers.

| Part | Basis |
|---|---|
| Tile origin, x/z quantisation | [D 779/779] NAVMESH.md |
| y = origin y + q / (u16 at header +0x46) | [D]: ground fit on 8 sample tiles, live soldiers within ~0.3 m of the mesh |
| A* over portal midpoints, length costs | [V graph shape, I costs] NAVMESH.md kind 0 |
| Links across tiles / pieces: probe 5 cm across a border edge | [I]: the `0x4000` link words are not decoded |
| Funnel + mesh-sampled shortcut | [I]: not the game's smoother |

## Accuracy against live
Single-waypoint fresh requests, largest x/z distance between the game's path and ours: 408 of 410 get a path; **median 0.08 m, 60 % within 0.1 m, 75 % within 0.5 m, 87 % within 1 m, p99 3.7 m, worst 11.8 m**. Most of these paths are short and nearly straight, so the median flatters the search: on the 14 paths over 15 m the median is 0.8 m and the worst 3.8 m. The two-waypoint and extended requests (most of the traffic) are **not compared yet**.

The test pins these numbers against regression. `test_gate_paths_equal_live` is a strict xfail: it fails today and will flag when it starts passing.

## Open (E33)
Navx search and smoother in the async job; `0x4000` tile-link words; two-waypoint and extending requests; snap radius; off-mesh links (a soldier climbs ~4 m at one spot at (-513, 325-328, 548), ladder or stairs [I]); class-to-type mapping and the 0x8000 type flag; `.frt` edge events → speed; route selection near the player.

---
<small>Source: `docs/engine/Navigation.md` in the project repository &middot; generated 2026-10-30.</small>
