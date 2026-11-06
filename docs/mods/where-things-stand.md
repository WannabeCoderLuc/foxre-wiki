# Where things stand for modders

*Hand-written overview, as of 2026-11-05 (M9 PASS, M10 PASS). What is decoded, what the new engine already runs, and what its Mod API offers. Order and gates: [Roadmap](../status/roadmap.md). Counts: [Numbers at a glance](../status/numbers.md).*

## Three levels
Every topic on this site sits at one of three levels:

| Level | Meaning | What a modder can do with it |
|---|---|---|
| **Decoded** | written down in a spec, with evidence and tags | use the facts in a mod for the original game |
| **Ported** | the new engine implements it and a test compares it with the real game | test ideas offline (inside the project for now) |
| **Extensible** | the engine offers a documented way for mods to add or change it | write a mod against the Mod API (M10 PASS; engine still private) |

The third level started with M10: the frame loop, messages and commands, DataSet classes, the Lua host and the soldier and base tables can be extended through the Mod API. The engine's own repository is private for now, so this is not yet usable outside the project.

## What is decoded and ported, by area
| Area | Decoded | Ported and tested | Guide |
|---|---|---|---|
| Archives (QAR) and packages (FPK / FPKD) | yes, every entry | read and write, byte-identical (134,241 entries, 16,354 packages) | [Archives, packages and hashes](archives-and-hashes.md) |
| DataSets (`.fox2`) and the class registry | yes, 1,153 classes | read and write (44,994 files); entity graph; live check on 17 objects | [Editing fox2 DataSets](editing-datasets.md) |
| Routes (`.frt`), navmeshes (`.nav2`) | yes | read and write (307, 840 files) | [Navmeshes and routes in a mod](navigation-and-routes.md) |
| Terrain (`.htre`, `.tre2`) | yes, heights and placement | read and write; ground height within 5 mm of live; runs in C++ (bit-identical) | [Ground height at any point](ground-height.md) |
| Collision (`.geom`, `.geoms`, `.gskl`) | container yes; shape payloads no (E30) | container read and write (5,176 files) | [Terrain and collision files in a mod](collision-files.md) |
| Object manager, update order, message bus | yes | yes, equal to live order | [Messages and commands in a mod](messages-and-commands.md) |
| Lua host: boot, natives map, messages, timers | yes (5,532 natives mapped) | boots the game's own scripts; natives answered from recordings | [Find and call Lua natives](lua-natives.md) |
| Mission load, packages, script blocks, iDroid reload | yes | yes, the live script order | [Add a package to a mission](add-a-package.md), [Side content with script blocks](script-blocks.md) |
| Locators and map blocks | yes | yes, live messages for both free-roam maps | [Locators and map blocks in a mod](locators-and-blocks.md) |
| Path finding | yes, six stages | 948 of 948 live jobs within 0.1 m; obstacles replayed from recordings; runs in C++ (about 19 times faster, bit-identical) | [Navmeshes and routes in a mod](navigation-and-routes.md) |
| Soldiers: far mode, route steps, CP phases, reports, alert slow band | yes (M9 PASS) | realize budget, route steps, phase timers and reports, front point and slow band | [Soldiers and alert phases in a mod](soldier-ai.md) |
| Damage, combat, weapons, animation, physics, sound, UI drawing, rendering | no | no | PLANNED (M12 to M21) |

"Natives answered from recordings" means: when the game's Lua calls a native function the engine does not implement yet, the engine returns what the real game returned in a recorded session. From M10 on, each native gets an owning milestone that must implement it; the M17 headless slice runs with none recorded.

## The Mod API (M10, PASS)
Milestone **M10 Mod API core** came right after M9. All of its checks pass: the seven gate items and the common checks every milestone from M10 on must pass; the gate was accepted on 2026-11-05. What exists:

- **Registries for everything the engine runs**: ten kinds of tables (game object types, `SendCommand` handlers, message ids, updaters, AI tables, measured parameters, resource loaders, DataSet classes, Lua libraries, natives) plus hooks and message listeners. The original game's content is registered by a built-in `vanilla` mod through the same calls a mod makes.
- **A manifest and loader**: namespace, API version (0.1; exact match until 1.0 in M24), dependencies and order hints. The load order is documented and the same on every run and for every input order; refused sets are undone completely, and the error names the mod.
- **Extension kinds**, each tested by one of nine reference mods: a new system with a lifecycle, message listeners and own message ids, new object types with commands, command handler chaining, new DataSet classes, value overrides, before / after hooks that observe, change or cancel, AI table inserts, and Lua libraries.
- **Three hook sites**: a soldier's route switch, a base's phase change, and command dispatch.
- **Lua mods in a sandbox** (no files, OS, clock, `require` or precompiled code; 10 million instructions per call) and Python mods for your own prototypes.
- **A C++ backend** for ground heights and path finding, the default when built, checked bit for bit against the Python reference ([The C++ backend](../explain/native-backend.md)).

| Check | What the test checks | Status |
|---|---|---|
| G1 Registries | every table goes through the registry and equals its source; all earlier gates still pass | <span class="status pass">PASS</span> |
| G2 Null mod | an empty mod changes nothing: frame loop, script host and soldier traces byte-identical | <span class="status pass">PASS</span> |
| G3 Reference mods | nine mods, one per kind, each against a fixture; for example an alert rate of 1/20 instead of 1/30 ends the recorded alert after 1,199 frames instead of 1,798, exactly as predicted | <span class="status pass">PASS</span> |
| G4 Rejections | name and hash collisions, version mismatch, missing dependency, cycles, sandbox escapes, nondeterminism are refused with the mod named | <span class="status pass">PASS</span> |
| G5 Load order | two mods on one value or one hook site resolve the same way for every input order and run | <span class="status pass">PASS</span> |
| G6 Overhead | registry reads cost at most 5 % frame time (measured about 0.5 to 3 %) | <span class="status pass">PASS</span> |
| G7 Ownership | each of the 5,532 natives and 514 command handlers has the milestone that must implement it | <span class="status pass">PASS</span> |
| C1 Suite | the whole test suite passes | <span class="status pass">PASS</span> |
| C2 Specs | every touched specification says how mods can extend it | <span class="status pass">PASS</span> |
| C3 Natives | the milestone owns no natives to implement | does not apply |
| C4 Determinism | 24 scenarios, run twice and in a second process, byte-identical | <span class="status pass">PASS</span> |
| C5 Fixtures | the 18 recordings the tests use come from agreeing live runs, or the reason is written down | <span class="status pass">PASS</span> |
| C6 Mods | a reference mod for each extension point; the empty mod changes nothing | <span class="status pass">PASS</span> |
| C7 C++ backend | the C++ copies give bit-identical answers to the Python reference | <span class="status pass">PASS</span> |
| C8 Docs | these hand-written pages rewritten; the site builds with no warnings | <span class="status pass">PASS</span> |

Background and limits: [How mods plug into the engine](../explain/mod-api.md). Writing one: [Writing a mod for the new engine](mod-api.md).

## Later mod milestones (planned)
| Milestone | For modders |
|---|---|
| M11 Asset formats | readers and writers for textures, models, skeletons, outfits, language and sound containers |
| MOD-B AI sandbox (after M9, M10) | predict a behaviour or route change in the engine before testing it in the game |
| MOD-C Content importers (after M11, M16, M24) | glTF to model and skeleton, PNG to texture, glTF animation to the game's animation format |
| MOD-D World authoring (after M8, M13, M14) | new terrain, navmeshes, map-block grids, locators and routes |
| MOD-E Enhanced renderer (after M20) | modern lighting and effects as a separate mode |
| M24 Mod platform 1.0 | frozen, versioned API; asset packs; native plugins through a C interface; a mod manager; one example mod per area |

MOD-A, tools for the original game (validated file writers, a route editor, a navmesh baker, a mod-Lua test harness), is **in scope since 2026-11-05** (IN PROGRESS): **G1 PASS (2026-11-06)**, the validated writers for route sets, DataSets and packages and the `.frt` route editor ([Mod toolkit](../engine/mod-toolkit.md)); the navmesh baker (G2), the mod-Lua harness (G3) and the in-game check (G4) are PLANNED. Each tool is checked offline against the engine first (the baker, for example, must answer at least 1,000 path queries within 0.1 m of the game's own navmesh), then its output is loaded and tested in the game.

## Promises the engine makes
- **Compat mode**: with no mods loaded, every test against the original game still passes. Enhanced features are separate modes.
- **Determinism**: randomness only from the engine's seeded generator, a fixed frame order. A mod's effect can be replayed exactly.
- **Extension points in every spec**: each engine and format spec has a section saying what a mod can register, override, hook or replace; the index is the [Mod API](../engine/mod-api.md) reference page.
- **Nothing changes by accident**: with an empty mod loaded every test passes byte for byte; a mod's changes are owner-tagged and can be listed.

## How this would be used in a mod
*Hypothetical and untested: no such mod exists.* Someone planning a "longer alerts" mod for the original game could first try the idea in the engine: override the alert rate parameter, run the recorded Soviet-base alert, and read off the new length before touching the game. The engine's tests show the method works for the faster direction (1,199 instead of 1,798 frames at 1/20). Moving the same change into the original game would still need a Lua or native mod there and an in-game test; that comparison is the planned MOD-B item.

## What you can use today, for the original game
- The **findings** in the guides, for Lua mods and native hooks (with your own testing).
- The **specs** in the Reference sections, for your own file tools.
- The **claims ledger**, to check community addresses before hooking them.

---
<small>Hand-written article (`docs/site/mods/Where-Things-Stand.md`) &middot; published 2026-11-06.</small>
