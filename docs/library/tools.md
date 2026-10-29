# Tools

*Hand-written index. Full inventories: [MCP server and knowledge DB](mcp-server.md), [Installed tools](tooling.md).*

## Built in this project
| Tool | What it does |
|---|---|
| `Engine/formats/` | byte-exact readers and writers: QAR, FPK, FOX2, FRT, NAV2 |
| `Engine/core/` | StrCode / PathCode hashes (verified against the game in an emulator), type DB, entity graph |
| `Engine/script/` | the Lua 5.1 script host with the game's API surface and record/replay |
| `Engine/resources/` | package loader, mission blocks, script blocks, iDroid UI |
| `Engine/runtime/` | game object manager, update scheduler, message bus |
| FoxTrace (`Tools/FoxTrace/`) | log-only IHHook plugin: function hooks, Lua native return recording ([guide](../mods/foxtrace.md)) |
| `mgsv-unified` MCP server | gives the AI agent decompilation, cross-references, the knowledge DB, oracles and the live game |
| `Tools/claims_import.py` | imports and checks community claims ([ledger](../engine/claims.md)) |
| `Tools/static_lua_consts.py` | reads Lua constant tables straight from the executable |

## Third-party tools
Ghidra 12.1.4 (with pyghidra), unicorn (single-function emulation), capstone, lief, keystone, Kaitai Struct, lupa (Lua 5.1 in Python), pytest, MinHook, MSVC 2022, ImHex, RenderDoc, Blender. Lessons on test-gated AI-assisted reverse engineering: [Installed tools](tooling.md).

---
<small>Hand-written article (`docs/site/library/Tools.md`) &middot; published 2026-10-29.</small>
