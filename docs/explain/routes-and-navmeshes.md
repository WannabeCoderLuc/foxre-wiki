# Routes and navmeshes

*Formats decoded in M1; their runtime use belongs to M8 (Navigation and routes). References: [FRT route sets](../formats/frt.md), [NAV2 navmeshes](../formats/nav2.md).*

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

## Still open
The runtime side: path queries, how a soldier follows a route and fires its events, and 35 event types whose names are unknown. That is M8 work.

---
<small>Hand-written article (`docs/site/explain/Routes-And-Navmeshes.md`) &middot; published 2026-10-30.</small>
