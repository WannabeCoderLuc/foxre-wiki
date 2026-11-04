# Where things stand for modders

*Hand-written overview, as of 2026-11-04 (M9 PASS, M10 next). What is decoded, what the new engine already runs, and what the planned Mod API will offer. Order and gates: [Roadmap](../status/roadmap.md). Counts: [Numbers at a glance](../status/numbers.md).*

## Three levels
Every topic on this site sits at one of three levels:

| Level | Meaning | What a modder can do with it |
|---|---|---|
| **Decoded** | written down in a spec, with evidence and tags | use the facts in a mod for the original game |
| **Ported** | the new engine implements it and a test compares it with the real game | test ideas offline (inside the project for now) |
| **Extensible** | the engine offers a documented way for mods to add or change it | nothing yet: the Mod API is PLANNED (M10) |

Nothing is at the third level yet. The engine's own repository is private for now.

## What is decoded and ported, by area
| Area | Decoded | Ported and tested | Guide |
|---|---|---|---|
| Archives (QAR) and packages (FPK / FPKD) | yes, every entry | read and write, byte-identical (134,241 entries, 16,354 packages) | [Archives, packages and hashes](archives-and-hashes.md) |
| DataSets (`.fox2`) and the class registry | yes, 1,153 classes | read and write (44,994 files); entity graph; live check on 17 objects | [Editing fox2 DataSets](editing-datasets.md) |
| Routes (`.frt`), navmeshes (`.nav2`) | yes | read and write (307, 840 files) | [Navmeshes and routes in a mod](navigation-and-routes.md) |
| Terrain (`.htre`, `.tre2`) | yes, heights and placement | read and write; ground height within 5 mm of live | [Ground height at any point](ground-height.md) |
| Collision (`.geom`, `.geoms`, `.gskl`) | container yes; shape payloads no (E30) | container read and write (5,176 files) | [Terrain and collision files in a mod](collision-files.md) |
| Object manager, update order, message bus | yes | yes, equal to live order | [Messages and commands in a mod](messages-and-commands.md) |
| Lua host: boot, natives map, messages, timers | yes (5,532 natives mapped) | boots the game's own scripts; natives answered from recordings | [Find and call Lua natives](lua-natives.md) |
| Mission load, packages, script blocks, iDroid reload | yes | yes, the live script order | [Add a package to a mission](add-a-package.md), [Side content with script blocks](script-blocks.md) |
| Locators and map blocks | yes | yes, live messages for both free-roam maps | [Locators and map blocks in a mod](locators-and-blocks.md) |
| Path finding | yes, six stages | 948 of 948 live jobs within 0.1 m; obstacles replayed from recordings | [Navmeshes and routes in a mod](navigation-and-routes.md) |
| Soldiers: far mode, route steps, CP phases, reports, alert slow band | yes (M9 PASS) | realize budget, route steps, phase timers and reports, front point and slow band | [Soldiers and alert phases in a mod](soldier-ai.md) |
| Damage, combat, weapons, animation, physics, sound, UI drawing, rendering | no | no | PLANNED (M12 to M21) |

"Natives answered from recordings" means: when the game's Lua calls a native function the engine does not implement yet, the engine returns what the real game returned in a recorded session. From M10 on, each native gets an owning milestone that must implement it; the M17 headless slice runs with none recorded.

## What the Mod API will offer (planned)
Milestone **M10 Mod API core** comes right after M9. None of it exists yet. Planned, per the roadmap:

- **Registries for everything.** Game object types, `SendCommand` handlers, message ids, updaters, AI node tables, resource loaders, DataSet classes and Lua libraries are registered, not hardcoded. The original game's content registers through the same path as a mod.
- **A mod manifest**: namespace, API version (0.x until M24), dependencies, load order. A loader detects conflicts.
- **Extension kinds**: a new system with its own update and the `OnAllocate` / `OnInitialize` / `OnUpdate` / `OnTerminate` lifecycle; message listeners and own message ids; new game object types with command handlers; new `.fox2` classes; parameter overrides layered by load order; before / after hooks that can observe, change or cancel; command handler chaining; AI node insert or replace; Lua libraries.
- **Lua mods in a sandbox** (no `os`, `io`, `debug`, `require` or binary chunks) and Python mods for prototypes.

How M10 will be tested (gate items, abbreviated):

| Item | Test |
|---|---|
| Registries | every type, handler, message, updater and Lua library goes through the registry; all earlier gates still pass |
| Null mod | the whole suite with an empty mod loaded gives byte-identical traces |
| Reference mods | one per extension kind, for example a morale system on CP phases, or a phase rate override that changes the phase trace by exactly the predicted amount |
| Rejections | id collisions, API mismatch, missing dependency, load-order cycles, sandbox escapes and unseeded randomness are refused |
| Load order | two mods overriding one value resolve the same way every run |
| Overhead | registry dispatch costs at most 5 % frame time |

## Later mod milestones (planned)
| Milestone | For modders |
|---|---|
| M11 Asset formats | readers and writers for textures, models, skeletons, outfits, language and sound containers |
| MOD-B AI sandbox (after M9, M10) | predict a behaviour or route change in the engine before testing it in the game |
| MOD-C Content importers (after M11, M16, M24) | glTF to model and skeleton, PNG to texture, glTF animation to the game's animation format |
| MOD-D World authoring (after M8, M13, M14) | new terrain, navmeshes, map-block grids, locators and routes |
| MOD-E Enhanced renderer (after M20) | modern lighting and effects as a separate mode |
| M24 Mod platform 1.0 | frozen, versioned API; asset packs; native plugins through a C interface; a mod manager; one example mod per area |

MOD-A, tools whose output is tested in the original game (a route editor, a navmesh baker, a mod-Lua test harness), is **not planned for now**.

## Promises the engine makes
- **Compat mode**: with no mods loaded, every test against the original game still passes. Enhanced features are separate modes.
- **Determinism**: randomness only from the engine's seeded generator, a fixed frame order. A mod's effect can be replayed exactly.
- **Extension points in every spec**: each engine and format spec gets a section saying what a mod can register, override, hook or replace. The soldier spec already has one ([Soldier AI](../engine/soldier-ai.md), "Extension points").

## What you can use today, for the original game
- The **findings** in the guides, for Lua mods and native hooks (with your own testing).
- The **specs** in the Reference sections, for your own file tools.
- The **claims ledger**, to check community addresses before hooking them.

---
<small>Hand-written article (`docs/site/mods/Where-Things-Stand.md`) &middot; published 2026-11-04.</small>
