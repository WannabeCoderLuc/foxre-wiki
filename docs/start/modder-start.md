# Getting started as a modder

*Hand-written. For people who mod MGSV:TPP today, or plan to mod the new engine later. Addresses are for PC Steam 1.0.15.4 EN.*

## What this site gives you
This project does not ship a mod tool for the original game. It gives you **checked knowledge** that mod tools and mods can build on:

- **File formats** read and written back byte for byte, for every file of that type in the game ([Reference: file formats](../formats/qar.md)).
- **How the game's systems work**, from mission loading to soldier alert phases, each with the evidence behind it ([Explanations](../explain/game-data.md)).
- **Modding guides** that turn those findings into practical advice, with a worked example per topic ([Modding guides](../mods/for-modders.md)).
- **Checked addresses**: community addresses tested against the executable ([Checking community addresses](../mods/claims.md)).
- Later, a **new engine with a Mod API** (planned for M10, frozen as 1.0 in M24). See [Where things stand for modders](../mods/where-things-stand.md).

## Pick your path
| You want to | Start with | Then |
|---|---|---|
| Add content to a mission (props, scripts) | [Add a package to a mission](../mods/add-a-package.md) | [Run your own Lua from a package](../mods/lua-from-packages.md) |
| Write side content that loads with an area | [Side content with script blocks](../mods/script-blocks.md) | [Locators and map blocks in a mod](../mods/locators-and-blocks.md) |
| React to game events from Lua | [Messages and commands in a mod](../mods/messages-and-commands.md) | [Find and call Lua natives](../mods/lua-natives.md) |
| Change patrols or soldier behaviour | [Navmeshes and routes in a mod](../mods/navigation-and-routes.md) | [Soldiers and alert phases in a mod](../mods/soldier-ai.md) |
| Place objects on the ground | [Ground height at any point](../mods/ground-height.md) | [Terrain and collision files in a mod](../mods/collision-files.md) |
| Write a file tool | [Archives, packages and hashes](../mods/archives-and-hashes.md) | [Editing fox2 DataSets](../mods/editing-datasets.md) |
| Hook native code | [Checking community addresses](../mods/claims.md) | [Tracing the game with FoxTrace](../mods/foxtrace.md) |
| Patch menus | [Patching the iDroid tables](../mods/idroid-tables.md) | [The iDroid and the language reload](../explain/idroid.md) |

## Five things to know first
1. **Lua decides what, the executable decides how.** Missions, package lists, phase commands and most game rules are Lua. Much of what a mod wants is reachable from Lua without touching native code ([The Lua script host](../explain/script-host.md)).
2. **Names are hashes.** Files are found by a 64-bit path hash, most other names by a 32- or 64-bit string hash. A number where you expect a name is usually a hash ([Addresses, hashes and tags](conventions.md)).
3. **Packages run their own Lua.** Every `.lua` inside a package runs when the package loads. That is the cleanest way to get your code into the game ([How a mission loads](../explain/mission-load.md)).
4. **Read the tags.** [V] is checked in code or live, [D] holds for every game file, [I] is a likely explanation, [?] is open. Build on [V] and [D]; test [I] yourself.
5. **The Lua examples on this site are hypothetical.** Each guide ends with "How this would be used in a mod". Those examples show how a finding would be applied; none of them was built or tested by this project.

## Rules this project follows (and recommends)
- The game executable is never modified. Changes go through runtime hooks (an IHHook plugin, MinHook) or Lua.
- Offline single player only. Online play and FOBs are out of scope.
- Keep a clean copy of the game and restore it after tests.
- Never save during a test run that changes life, clock or weather: those values go into the checkpoint ([Soldiers and alert phases in a mod](../mods/soldier-ai.md), "Testing near soldiers").

## Tools you will meet here
| Tool | Role |
|---|---|
| Infinite Heaven, IHHook | community Lua framework and plugin loader; this project uses IHHook's Lua pipe for live checks |
| SnakeBite | community installer for `.mgsv` packages |
| GzsTool, FoxTool | community archive and DataSet tools; their name dictionaries are reused here |
| FoxTrace | this project's log-only hook plugin ([guide](../mods/foxtrace.md)) |
| `Engine/` | this project's readers, writers and script host (private repository for now) |

## Next
- Words you do not know: [Glossary](glossary.md).
- How addresses, hashes and tags are written: [Addresses, hashes and tags](conventions.md).
- What exists today and what is planned: [Where things stand for modders](../mods/where-things-stand.md).

---
<small>Hand-written article (`docs/site/start/Modder-Start.md`) &middot; published 2026-11-05.</small>
