# Tools

*Hand-written index. For modders, the readers and the hash functions are the parts that matter most ([Archives, packages and hashes](../mods/archives-and-hashes.md)). Full inventories: [MCP server and knowledge DB](mcp-server.md), [Installed tools](tooling.md).*

## Built in this project
| Tool | What it does |
|---|---|
| `Engine/formats/` | byte-exact readers and writers: QAR, FPK, FOX2, FRT, NAV2, FoxData (terrain and collision containers), typed terrain |
| `Engine/core/` | StrCode / PathCode hashes (verified against the game in an emulator), type DB, entity graph |
| `Engine/script/` | the Lua 5.1 script host with the game's API surface and record/replay |
| `Engine/resources/` | package loader, mission blocks, script blocks, iDroid UI |
| `Engine/runtime/` | game object manager, update scheduler, message bus, timers, popups, title flow |
| `Engine/world/` | locators and stage blocks (M6), ground height (M7), path finding (M8), soldier realize selection, route steps and CP phases (M9) |
| `Engine/tests/` and `gates.json` | the test suite and the list of gate items per milestone; `engine_verify(gate="M9")` reports each item |
| FoxTrace (`Tools/FoxTrace/`) | log-only IHHook plugin: function hooks, Lua native return recording, and from version 3.1 to 3.3 soldier, route, CP phase, notice and radio loggers ([guide](../mods/foxtrace.md)) |
| `Tools/m9_run.py` and run plans | drives one live soldier run under the capture protocol and restores the game afterwards |
| `mgsv-unified` MCP server | gives the AI agent decompilation, cross-references, the knowledge DB, oracles and the live game |
| `Tools/claims_import.py` | imports and checks community claims ([ledger](../engine/claims.md)) |
| `Tools/static_lua_consts.py` | reads Lua constant tables straight from the executable |
| foxagent | a cited search over the project's own documents, decompiles and data, used by the agent to answer questions from what is already known |

## Third-party tools
Ghidra 12.1.4 (with pyghidra), unicorn (single-function emulation), capstone, lief, keystone, Kaitai Struct, lupa (Lua 5.1 in Python), pytest, MinHook, MSVC 2022, ImHex, RenderDoc, Blender. Lessons on test-gated AI-assisted reverse engineering: [Installed tools](tooling.md).

---
<small>Hand-written article (`docs/site/library/Tools.md`) &middot; published 2026-11-06.</small>
