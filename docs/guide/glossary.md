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
| **Gate** | the automated pass/fail test that closes a milestone |
| **Round trip** | read then re-write a file and require identical bytes |
| **Oracle** | a trusted reference to compare against (the original function, or the running game) |
| **Clean-room** | re-implementing from written specifications only, never from copied code |

---
<small>Source: `docs/guide/Glossary.md` in the project repository &middot; generated 2026-10-24.</small>
