# Routes and navmeshes

*Formats decoded in M1, path finding in M8 (PASS 2026-11-01). In depth: [How soldiers find their way](path-finding.md), [How soldiers think](soldier-ai.md). References: [FRT route sets](../formats/frt.md), [NAV2 navmeshes](../formats/nav2.md), [Navigation and routes](../engine/navigation.md).*

## What they are
Two kinds of data tell characters where they can and should go:

- **Navmeshes** (`.nav2`) describe the **walkable surface**: triangles grouped into regions, with links between neighbours. Path finding searches this graph.
- **Route sets** (`.frt`) describe **intended paths**: a soldier's patrol, a vehicle's convoy, a guard's idle spots. A route is a list of points; each point and each stretch between points carries events such as "walk relaxed", "idle here", "aim at that spot" or "send a message".

## Why they matter
Without navmeshes nothing can path-find; without routes soldiers have nowhere to patrol. For mods they decide where new characters can walk (a large mech needs a mesh made for its size) and how existing ones behave.

## How the original does it
- **Worlds.** A `NavxNavBlock` entity in a block DataSet names a navmesh file, its tile and its *world*. The game has only three worlds: the default one (666 tiles, the whole map, used by soldiers and vehicles), `sky` (air units) and `sahelan` (only the Episode 31 arena). A character binds to a world by name when its navigation controller is created.
- **Tiles.** The default world is cut into 640 m tiles generated for an agent of radius 8 and height 25; each tile is one `.nav2` file with a spatial grid for fast lookups.
- **Routes.** Every `.frt` file holds many routes: across the game 104,653 routes, 604,395 points and 963,624 events of 104 types (the 15 most common are relaxed/caution idles and walks, vehicle moves and `SendMessage`). Route names are stored as StrCode32 hashes; scripts switch soldiers between routes by name.

## How the new engine does it
Both formats have byte-identical readers and writers (`Engine/formats/frt.py`, `Engine/formats/nav2.py`): **307 of 307** route files and **840 of 840** navmeshes re-encode unchanged. Values the engine computes at build time (link weights, region-link costs) are fitted, not exact, so edits rescale them instead of recomputing.

- **Planning a path.** A far-away goal is searched in steps: first coarse clusters of the map, then regions inside them, then the small nodes inside those regions. The result is then smoothed: corners slide along triangle edges, straight shortcuts are tried, and short zigzags are stretched so a soldier does not twitch.
- **What is loaded matters.** Only the map blocks loaded around the player can be searched. A soldier starting outside them just gets a straight line, which is how most far soldiers move.
- **The map changes while you play.** A parked truck blocks the triangles under it and adds a ring of four temporary points to walk around. Ladders and climbs are also temporary points, added as links between two places on the mesh. The search treats these like the rest of the graph.

## How we know
FoxTrace logs every path job in the real game, with its inputs and the state of the map at that moment. The engine then gets the same inputs and must produce the same path: **948 of 948 jobs match within 10 cm** (Afghanistan free roam, patrol phase, player away from soldiers). Getting there exposed a mistake in our own logging: long jobs had been recorded before the game finished smoothing them, so those older recordings were replaced.

## Still open
- What creates the temporary state. The engine replays recorded obstacles and links; it cannot make them yet.
- How soldiers follow routes close to the player. Far away they slide exactly along the route at 0.80 m/s; close up they walk at about 1.0 m/s and stray from it. This moved to M9 together with soldier behaviour.
- Other missions, Africa, Mother Base and alert phases are not tested yet.

## For modders
- Route commands, writing routes, why far soldiers ignore walls: [Navmeshes and routes in a mod](../mods/navigation-and-routes.md).
- Reading and writing `.frt` and `.nav2` files byte-exactly: [FRT route sets](../formats/frt.md), [NAV2 navmeshes](../formats/nav2.md). A navmesh baker and route editor for the original game (MOD-A) are not planned for now; world and navmesh authoring for the new engine is MOD-D ([Where things stand for modders](../mods/where-things-stand.md)).

---
<small>Hand-written article (`docs/site/explain/Routes-And-Navmeshes.md`) &middot; published 2026-11-04.</small>
