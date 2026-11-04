# How soldiers find their way

*M8, PASS on 2026-11-01. Background: [Routes and navmeshes](routes-and-navmeshes.md). Exact details: Navigation and routes, [NAV2 navmeshes](../formats/nav2.md), [FRT route sets](../formats/frt.md). Modding: [Navmeshes and routes in a mod](../mods/navigation-and-routes.md).*

## What it is
When a soldier has to walk somewhere, the game answers one question: which line through the world gets there without walking through a wall? That answer is a **path job**. It takes a start, a goal and some rules, and it returns a short list of points. This page follows one job from request to result, then looks at what can change the answer.

## Why it matters
An engine that wants soldiers in the same places as the real game must plan the same paths. Small differences grow: a soldier on another corner sees other things and reaches its next point at another time. For modders, these rules explain why a character takes a strange line, ignores a wall or walks through a building far away.

## How the original does it

### From a request to a job
Everything goes through `RequestMove` on the navigation controller [V]. It snaps the goal to the mesh, then asks the planner to start a path. The planner makes one decision first:

- **Start outside the loaded map blocks:** no search. The path is one straight line.
- **Start on a loaded navmesh:** a search job is queued and runs over several frames.

This first decision matters more than anything else on this page. In the clean capture, **3,865 of 4,162 finished jobs (93 %) were straight lines** [D], because most soldiers were far from the player. Far soldiers really do walk straight through the map, and nobody is there to see it.

### The six stages
| Stage | What it does | Why |
|---|---|---|
| 1 | Finds the triangles under start and goal, and lists their edge points | Gives the search somewhere to begin and end |
| 2 | Plain A* search, only if start and goal are under 80 m apart, at most 512 nodes | Short trips need nothing more; on success it jumps to stage 6 |
| 3 | A* over coarse clusters of the map, at most 8 tiles and 32 clusters | Finds roughly which part of the map to cross |
| 4 | A* over regions inside those clusters, building a corridor of up to 64 regions | Narrows the route |
| 5 | A* over nodes, only inside the corridor | The precise search, kept cheap by stages 3 and 4 |
| 6 | Post-processing | Turns a list of edge points into a line a soldier can walk |

A* is the standard method: always continue from the point with the lowest "cost so far + straight distance left". The game adds one detail an engine must copy: it rounds the cost to 0.01 at every step. Without that, equal-looking routes tie differently and the search picks another one.

### Long trips are not finished trips
If the search runs out of its limits, the cluster where it stopped becomes a temporary goal. The soldier gets a path towards it and the rest is planned later. So a long path may not contain its goal at all [V]. This is normal behaviour, not a failed search.

### Smoothing: why corners sit in odd places
The raw result runs through triangle edges and looks jagged. Soldiers use four smoothing steps [V, D]:

1. **Collect** the node positions, dropping duplicates, and add the goal.
2. **Slide.** Up to 10 passes: each point moves to where the line from the previous to the next point crosses its triangle edge, staying 2 cm from the edge's ends. That is why corners sit partway along edges, not on vertices.
3. **Shortcut.** First try a straight ray from start to goal. Otherwise walk along the points and keep only those needed to stay in sight of each other.
4. **Stretch.** Pieces under 4 m are replaced by the crossing of the lines around them, or lengthened to exactly 4 m. That is why a soldier's first corner is so often exactly 4 m away.

### The map changes while you play
A path depends on the moment, not only on the file on disk [V, D]:

- **Blocked triangles and links.** They appear where vehicles stand and toggle during play.
- **Obstacle rings.** An active obstacle gets a ring of 4 temporary nodes, so paths go round it. A goal inside its box has no goal nodes.
- **Off-mesh links.** Temporary link pairs join two places on the mesh, for example (530.0, 320.2, 1151.7) to (529.5, 324.0, 1150.2), a rise of nearly 4 m. Which game objects create them is still open.

### Re-requests
A soldier already walking does not restart from its feet. The new search starts about 5 m further along the old path, and the old part stays in the result, so the first path point is not the search's start [V]. Requests with two waypoints also start a hidden job for the next leg.

### Routes and path jobs together
Routes say where a soldier wants to go; path jobs say how to get there. Each leg of a route sends exactly **one** `RequestMove` when it starts, using the soldier's index as the slot: 673 of 673 legs in two runs [V, D]. Vehicle riders send none (450 of 450). The full step machine is on [How soldiers think](soldier-ai.md).

## How the new engine does it
`Engine/world/navigation.py` has all six stages, the smoothing and the runtime rules, in 32-bit floats like the game. It is told which blocks are loaded and what the runtime state is, then calls `find_path(start, goal, filter=, cost_mult=, cost_mask=)`.

It does not yet create the runtime state itself. Blocked triangles, rings and links come from the recording of each job, so the engine cannot plan on its own in a world with moving trucks.

## How we know
FoxTrace logs each job in the real game, with its exact input, output and the runtime state at its start. The engine gets the same input.

**948 of 948 jobs match within 10 cm** (639 searched, 25 of them coarse; 309 straight). The last run was captured after the last code change and matched with no fixes, so it was a real test and not something the code had been tuned to [D].

Three mistakes in our own logging looked like engine errors for a long time, and are worth knowing if you trace paths yourself:

- The smoothing can run over several frames. Recording at "search finished" saved half-finished paths. Captures before `m8_nav10` cannot be used.
- Loaded blocks and obstacles must be read when the job starts. Read at its end they are out of date by a frame or more.
- Pairing a request with "the next path seen" can pick up another leg's result.

## Still open
- What creates blocked triangles, obstacle rings and off-mesh links; who adds the blocked link pairs [?].
- Cluster-level dynamic links are not ported; no recorded job needed them.
- All captures are Afghanistan, mission 30010, sneak phase. Alert, other missions, Africa and Mother Base are untested.

---
<small>Hand-written article (`docs/site/explain/Path-Finding.md`) &middot; published 2026-11-04.</small>
