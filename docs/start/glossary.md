# Glossary

*Hand-written. Short definitions of the terms used on this site, grouped by topic. Notation for addresses and hashes: [Addresses, hashes and tags](conventions.md).*

## Files and data
| Term | Meaning |
|---|---|
| **Fox Engine** | Konami's game engine used by MGSV:TPP, Ground Zeroes and Metal Gear Survive |
| **QAR** | the large archive format of `master\*.dat`; entries are keyed by path hash |
| **FPK / FPKD** | packages inside archives; FPKD holds the DataSets, FPK the assets. The game loads a package as a whole |
| **DataSet (.fox2)** | a file describing entities and their properties, e.g. a level section. `.parts`, `.sim`, `.ph` and others are DataSets too |
| **Entity** | one object in a DataSet: a class plus property values |
| **Class / property** | the type of an entity and its named fields, as listed in the engine's class registry |
| **Reflection** | the engine's ability to describe its own classes and properties at runtime |
| **EntityPtr / Handle / Link** | the three kinds of reference between entities (owned, known, named in another file) |
| **FoxData** | the node-tree container shared by terrain (`.htre`, `.tre2`) and collision (`.geom`, `.geoms`, `.gskl`) files |
| **Route set (.frt)** | patrol paths: nodes, edges and the events that run on them |
| **Navmesh (.nav2)** | walkable surface data for path finding |
| **StrCode32 / StrCode64** | the engine's string hashes (32 bits, or 64 with 48 used in DataSets) used instead of names |
| **PathCode64** | the hash of a file path used as the archive entry key |
| **Round trip** | read then re-write a file and require identical bytes |

## Runtime
| Term | Meaning |
|---|---|
| **Frame** | one pass of the game loop, about 1/60 s; reference pages count time in frames |
| **Updater** | a system called once per frame, in priority order |
| **Game object** | an actor in the world (player, soldier, vehicle ...) with a 16-bit id (type and instance) |
| **Type manager** | the code object that runs all game objects of one type and answers their commands |
| **Message bus** | the engine's event system; messages carry up to 4 tagged arguments, 128 per queue |
| **SendCommand / SendMessage** | Lua functions to call into (at once) or queue data for (later) one game object |
| **OnMessage** | the mission script function that receives bus messages; returning 1 hands a message back |
| **Native** | a Lua function implemented in the executable; the game registers 5,532 of them |
| **Binding map** | the project's list of every native with its library, name and address |
| **Script resource** | a `.lua` file inside a package; it runs when the package loads |
| **Block / block group** | a memory region the engine loads packages into (location, mission, script blocks) |
| **Script block** | one of 8 global slots for side content (quests, reinforcements, animals) with its own script |
| **iDroid (MbDvc)** | the in-game device UI; its tables reload on every language change |

## World
| Term | Meaning |
|---|---|
| **Location / mission** | the map (`afgh`, `mafr`, `cypr`) and what runs on it (f30010 = Afghanistan free roam) |
| **Stage block (small block)** | a 128 m square of the map; a 5 × 5 window of them is loaded around one position |
| **Large block** | a big area such as a base, loaded when its small blocks come near the window |
| **DataIdentifier** | an entity that names other entities so scripts can find them; exists while its DataSet is loaded |
| **Locator** | an entity with a position that places something in the world (a soldier, a spot); scripts often find it through a DataIdentifier |
| **Heli space** | the helicopter "mission" between missions and on the title screen |

## Soldiers (M9)
| Term | Meaning |
|---|---|
| **CP (command post)** | the group that owns a base's soldiers and its alert phase, e.g. `afgh_sovietBase_cp` |
| **Phase** | a CP's state: 0 sneak, 1 caution, 2 evasion, 3 alert |
| **Phase timer** | a 0-to-1 number per CP that drains at a rate per phase |
| **Report (radio request)** | a radio call a soldier makes for the CP; a phase ends when the right report finishes |
| **Investigator** | a soldier given the investigate role: it goes to the CP's search point; the next report waits for it |
| **Search point** | the place a CP sends investigators to; marking it done ends their role |
| **Realized / unrealized** | fully simulated (at most 18 at once) or moved along routes with simple fixed speeds |
| **Realize budget** | the 18 soldiers nearest the window centre that get full simulation each frame |
| **Route step machine** | the per-soldier state machine that walks route legs and runs node events |
| **Path job** | one request to plan a path on the navmesh, from request to smoothed result |
| **Notice** | a soldier detecting the player (by sight, in the runs so far) |

## Method
| Term | Meaning |
|---|---|
| **Gate** | the automated pass/fail test that closes a milestone; a list of numbered items, each decided by named tests |
| **Common gate** | the checks every milestone from M10 on must also pass (items C1 to C8 in the roadmap) |
| **Oracle** | a trusted reference to compare against (the original function, or the running game) |
| **Fixture** | recorded ground truth a test compares against, from at least two agreeing runs |
| **FoxTrace** | the project's log-only hook plugin; watches the game without changing it |
| **Capture protocol** | the rules for live runs near soldiers: the player cannot die, no saves, no hand input, marked events |
| **Record / replay** | answering a native function with what the real game returned in a recorded session |
| **Native boundary** | the line between the game's Lua and the engine's own code, where the engine answers calls |
| **Claim** | a fact from a community source; counts only after the project's own check confirms it |
| **Clean-room** | re-implementing from written specifications only, never from copied code |

## Mods
| Term | Meaning |
|---|---|
| **Mod API** | the engine's documented interface for mods (M10 first version, M24 frozen as 1.0) |
| **Extension point** | a place where a mod may add to or change an engine system: register something new, override a value, hook an event |
| **Registry** | a table of types, handlers, messages or updaters that vanilla and mods both register into |
| **Manifest** | a mod's declaration: namespace, API version, dependencies, load order |
| **Namespace** | a mod's unique lower-case name; every new name it registers starts with it (`morale.MoraleSystem`) |
| **Vanilla mod** | the built-in mod that registers the original game's content, through the same calls as any mod |
| **Override** | a mod replacing a registered value or handler; the last loaded mod wins, earlier layers are kept |
| **Hook site** | a named engine call where mods may run before / after functions (`route.switch`, `cp.phase_change`, `command.dispatch`) |
| **CANCEL** | what a before hook returns to stop the engine call at a hook site |
| **Reference mod** | a small mod the tests load to prove one extension kind works as predicted |
| **Sandbox** | the restricted Lua environment shared mods run in: no files, OS, clock or `require` |
| **Null mod** | an empty mod; loading it must change nothing |
| **Reference mod** | a small mod per extension kind that the engine's tests run |
| **Compat mode** | the engine with no mods loaded; it must behave exactly like the original game |

---
<small>Hand-written article (`docs/site/start/Glossary.md`) &middot; published 2026-11-05.</small>
