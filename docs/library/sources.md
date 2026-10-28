# Sources

*Hand-written index of what the project's findings are built on. Community facts enter as claims and count only after our own checks ([Claims ledger](../engine/claims.md)).*

## Primary sources
| Source | What it gives us | How it is used |
|---|---|---|
| `mgsvtpp.exe`, PC Steam 1.0.15.4 EN | the engine and game code | static reading only (Ghidra, capstone), never modified; single functions run in an emulator as oracles |
| The game's data (`master\*.dat`) | every file the game loads | read-only; formats verified on every file; nothing published |
| The running game, offline single player | live behaviour | Lua through IHHook's pipe, log-only FoxTrace hooks; captures run twice and archived |
| `Fox.ExportSerializeInfo()` | the engine's own class registry (1,153 classes) | exported from the game itself, see [Reflection](../engine/reflection.md) |

## Community projects
| Project | Author | What we take from it |
|---|---|---|
| Infinite Heaven (r267) | TinManTex | Lua framework and module loader; its Lua is a source of claims (enums, hashes, behaviour notes) |
| IHHook (r25) | TinManTex | plugin loader and Lua pipe; its 1.0.15.4 address table and byte patterns are claims |
| V_Framework (1.6) | Yazed0071 | native framework; its address set and struct offsets are claims |
| GzsTool, FoxTool, FtexTool | Atvaark | archive/DataSet/texture tools and name dictionaries |
| FoxEngineTemplates | kapuragu | 010 Editor templates, cross-check for layouts |
| `frt.bt` | youarebritish | route event field meanings (marked as community knowledge) |
| MGSV modding wiki | community | names and addresses (never treated as independent confirmation) |
| SnakeBite | community | `.mgsv` installer used by Luc |

## Name dictionaries
Path and string names come from hashing known strings: GzsTool's `qar_dictionary` / `fpk_dictionary`, FoxTool's `fox_dictionary`, `mgsv-lookup-strings`, plus our own brute-forced names (`strcode_bruteforced.tsv`). 83 % of archive entries have a known name.

---
<small>Hand-written article (`docs/site/library/Sources.md`) &middot; published 2026-10-28.</small>
