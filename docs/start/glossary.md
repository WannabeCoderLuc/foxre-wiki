# Glossary

| Term | Meaning |
|---|---|
| **Fox Engine** | Konami's game engine used by MGSV:TPP, Ground Zeroes and Metal Gear Survive |
| **QAR** | the large archive format of `master\*.dat` |
| **FPK / FPKD** | packages inside archives; FPKD holds the DataSets, FPK the assets |
| **DataSet (.fox2)** | a file describing entities and their properties, e.g. a level section |
| **Entity** | one object in a DataSet: a class plus property values |
| **Class / property** | the type of an entity and its named fields, as listed in the engine's class registry |
| **Reflection** | the engine's ability to describe its own classes and properties at runtime |
| **StrCode32 / StrCode64** | the engine's string hashes (32 or 48 bits) used instead of names |
| **PathCode64** | the hash of a file path used as the archive entry key |
| **EntityPtr / Handle / Link** | the three kinds of reference between entities (owned, known, named in another file) |
| **Game object** | an actor in the world (player, soldier, vehicle ...) with a 16-bit id (type and instance) |
| **Type manager** | the code object that runs all game objects of one type |
| **Message bus** | the engine's event system; messages carry up to 4 tagged arguments |
| **SendCommand / SendMessage** | Lua functions to call into or queue data for one game object |
| **Route set (.frt)** | patrol paths with node and edge events |
| **Navmesh (.nav2)** | walkable surface data for path finding |
| **Gate** | the automated pass/fail test that closes a milestone; a list of numbered items, each decided by named tests |
| **Common gate** | the checks every milestone from M10 on must also pass (items C1 to C8 in the roadmap) |
| **Extension point** | a place where a mod may add to or change an engine system: register something new, override a value, hook an event |
| **Mod API** | the engine's documented interface for mods (M10 first version, M24 frozen as 1.0) |
| **Compat mode** | the engine with no mods loaded; it must behave exactly like the original game |
| **Round trip** | read then re-write a file and require identical bytes |
| **Oracle** | a trusted reference to compare against (the original function, or the running game) |
| **Clean-room** | re-implementing from written specifications only, never from copied code |
| **Script resource** | a `.lua` file inside a package; it runs when the package loads |
| **Block / block group** | a memory region the engine loads packages into (location, mission, script blocks) |
| **Script block** | one of 8 global slots for side content (quests, reinforcements, animals) with its own script |
| **iDroid (MbDvc)** | the in-game device UI; its tables reload on every language change |
| **Record / replay** | answering a native function with what the real game returned in a recorded session |
| **Native boundary** | the line between the game's Lua and the engine's own code, where the engine answers calls |

---
<small>Hand-written article (`docs/site/start/Glossary.md`) &middot; published 2026-11-04.</small>
