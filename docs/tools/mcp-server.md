# MCP server and knowledge DB

Single MCP endpoint for MGSV:TPP 1.0.15.4 EN work: static RE of `mgsvtpp.exe`, fox2 data, vanilla Lua, community wiki, V_Framework sources, `.nav2`, live game control, adapters, and the knowledge DB. Project rules in `..\CLAUDE.md` always win.

- Entry: `server\mgsv_unified_server.py` (stdio JSON-RPC, protocol 2024-11-05), run by `C:/Python313/python.exe`, registered in `..\.mcp.json` (+ `..\.agents\mcp_config.json`), enabled in `..\.claude\settings.local.json`. Restart the Claude session after changing tool schemas.
- Self-test: `python mgsv_unified_server\server\mgsv_unified_server.py --selftest` (must stay all-pass).
- Version 1.4.0, 30 tools. History: §8.

## 1. Which tool first
| Question | Start | Then |
|---|---|---|
| How does system X work? | `mgsv_explain_system(name)` | `mgsv_query_knowledge(docs, …)`, `re_class`, `re_decompile` |
| What is 0x…? | `mgsv_query_knowledge(functions, "0x…")` (dossier) | `re_decompile`, `re_xrefs`, `re_closure` |
| Callers / callees | `mgsv_query_knowledge(callers\|callees, va)` | `re_closure` (depth > 1) |
| Hash / string | `mgsv_query_knowledge(hashes, q)` | `re_hash` (slow live scan, also fox2) |
| SendCommand X | `mgsv_inspect_handler(X)` | `re_sendcommand`, `lua_search` |
| Vanilla Lua usage | `mgsv_query_knowledge(lua\|lua_api, q)` | `lua_search` (regex) |
| Functions by role | `mgsv_query_knowledge(functions, "role:<Role> text")` | `mgsv_query_knowledge(roles, "")` |
| Already researched? | `mgsv_query_knowledge(docs, words)` | read the doc section it names |
| Sahelan code/data | `sahelan_inventory` | |
| fox2 entities/props | `re_fox2` | |
| Navmesh | `navmesh_inspect` → edit → `navmesh_validate` (ship only `VALID`) | |
| Live game | `game_status` → `game_send_keys` / `game_pipe_lua` / `game_screenshot` | restore r5c after any run |

`mgsv_query_knowledge(all, q)` samples every category when you don't know where something lives.

## 2. Tool catalog
**Knowledge engine** (sub-second, `data\knowledge\mgsv_knowledge.db`)
- `mgsv_query_knowledge(query, category=all, limit=40 (≤300), abi=false)`. Categories: `functions` (VA → dossier; text or `role:` → list), `hashes`, `commands`, `classes`, `lua` (≥3 chars), `lua_api`, `docs` (FTS5: `a OR b`, `pre*`), `decomp`, `inventory`, `enums`, `modules`, `symbols`, `roles`, `callers`, `callees`, `ingested`, `all`.
  Roles: ActionController, NavigationController, StateCollector, NoticeController, DiscoveryController, AiController, AiModule, ActionPlugin, Action, DamageHandler, Realizer, MessageDispatch, Sound, Effect, Camera, Route, Weapon, Lifecycle, SendCommandHandler, LuaBinding, VFrameworkHook, VirtualMethod, HashUser.
- `mgsv_explain_system(system_name, depth=normal|full)`: docs, classes, functions by role, handlers, Lua API, hashes. Systems in `knowledge\systems.py` (Sahelanthropus AI, CommandPost2, Soldier NoticeController, Soldier2, Navmesh, Reinforcement, Walker Gear, Heli2, Vehicle, Player2, Buddies, UAV, Hostage2, Parasite2, Lua bindings, V_Framework, Fox2 data, Sound; aliases `sahelan`, `cp`, `notice`, `nav2`).
- `mgsv_inspect_handler(command_or_hash, decompile=false, lua_hits=8)`: hashes, handler(s), decompiled branch, code sites, every vanilla `{id="…"}` call with arg keys, V_F interception, docs.
- `mgsv_update_knowledge_db(mode=background|sync|status, force, only[], ingest_path)`.

**Static RE**
| Tool | Inputs | Notes |
|---|---|---|
| `re_decompile` | `va_or_name` | Ghidra server; FUN_ → names; hashes `/*"name"*/` (`s32` 32-bit match, `~` unverified candidate) |
| `re_decompile_batch` | `va_list`, `grep`, `head_lines` | `.c` → `data\re\decomp\mcp\` |
| `re_xrefs` | `va_or_name` | callers, refs, vtable slots, callees, hashes, ABI |
| `re_class` | name / vt / ctor / QI hash | vtables, ctors, slot map, `[rcx+disp]` fields |
| `re_field_access` | `offset_hex`, `region` (`sahelan\|nav\|action\|indexed`, `lo-hi`, function) | readers/writers |
| `re_hash` | `query`, `fox2` | ≤12 s scan |
| `re_fox2` | `query_type` (`classes\|class\|props\|value\|files\|file\|entity`), `target` (`entity` = `path#id`) | 5.4 GB fox2.db |
| `re_sendcommand` | `command`, `handler`, `context` | id → handler → branch |
| `re_closure` | `va`, `depth` 1–6, `mode` callees\|callers\|both, `limit` | |
| `sahelan_inventory` | `query`, `kind`, `tag`, `limit` | |
| `lua_search` | `pattern`, `path_filter`, `max_hits`, `context`, `include_mods` | regex |

**Docs:** `wiki_search(query)`, `wiki_read(article_name)` (178 community articles, not authoritative), `vframework_guide(topic)`, `vframework_search(query, mode=grep|commands|constants|address)` (AddressSet_day3900: first block EN, second JP).
**Navmesh:** `navmesh_inspect(file_path)`, `navmesh_validate(file_path)`.
**Live:** `game_status` (PID, focus, SHA1 + build tag of installed DLLs), `game_screenshot(output_path)`, `game_send_keys(sequence)` e.g. `"enter, wait 1000, NUMPAD8"`, `game_pipe_lua(lua_code)` (IHHook pipe).
**Adapters:** `atomizer_call(tool_function, arguments)` (`Tools\atom.py`), `websift_call(tool_name, arguments)` (`Tools\sift.mjs`).

**Engine oracles** (`server\oracle_tools.py`; machine-decidable PASS/FAIL, see [`..\docs\TOOLING.md`](tooling.md))
- `re_emulate(va, args, memory, max_insns)`: one function of the `GameBackup` `mgsvtpp.exe` in unicorn; sections mapped from the file (lief, relocs not parsed). Win64 ABI: args `int | "0x.." | "@buf" | "@buf+off" | "len:buf" | {"f": x} | {"f32": x}` → rcx/rdx/r8/r9 or xmm0-3 by position, the rest on the stack; `memory` = `[{name, hex|str|size, nul, align}]`. Returns status `ok|refused|insn_limit|error`, rax (+ u48/eax), xmm0, buffers after the call, insn count, writes into image sections (= not pure). Refused: execution outside `.xtext`, any touch of `.xdata`/`.ecode`/`.trace` (never mapped), import calls (IAT slots → trap addresses, reported by name), unmapped reads (gs:/TEB, heap).
  StrCode64: `0x141A09AC0(s, strlen)` (`ff_stringid_hash_n`) → `0x141A09770` `fox::StrCode64_Seeded(s, strlen+1, ((int8)s[0]<<16)+strlen)` (signed first byte). Body: CityHash 1.0.3 for ≤ 64 hashed bytes, CityHash 1.1 long-string loop above (0x141A08CB0 unaligned / 0x141A091F0 aligned, picked by pointer alignment). [V] `Tools\foxhash.py` == game for byte lengths 0–300 incl. non-ASCII (fixed 2026-10-21; verifier `Engine\tests\test_strcode64_oracle.py`). The game code is the oracle.
- `engine_verify(target, relock)`: pytest over `..\Engine\tests\` (or one file / dir / node id), junit → counts, `PASS`/`FAIL`. `Engine\tests\verifiers.lock.json` holds each verifier's sha256: changed/removed verifiers are reported and the lock is kept until `relock=true` (review first); new files are locked automatically.
- `lua51_run(code, files, stubs, max_insns)`: lupa Lua 5.1 without os/io/debug/package/require/dofile/loadfile/string.dump, no Python attribute access, text chunks only (bytecode refused), instruction limit. `files` = vanilla Lua (Assets-relative path or unique substring), each return value bound to the file's base name. `stubs` auto-creates unknown capitalised globals (a stub used as a number = 0); real `StrCode32/64` (+ `Fox.`), `bit` (LuaBitOp). Returns output, returns, errors, loaded, stubbed_globals.

Boundaries: paths resolve inside `C:\Users\Luc\Desktop\MetalGear` (traversal rejected). Only `game_send_keys`, `game_pipe_lua`, `game_screenshot` mutate; knowledge tools write only `data\knowledge\` and `logs\`; `engine_verify` writes `..\Engine\tests\verifiers.lock.json` and `logs\engine_verify_junit.xml`.

## 3. Evidence levels
- **Hash status:** `verified` (curated `strcode_bruteforced.tsv`, 48-bit StrCode64 match at a code/data site, or SendCommand id), `derived32` (low 32 bits of a verified name), `derived64` (StrCode64 of a command id), `site-match32`, `lua_literal` (unverified), `lua_literal+site` (also in code; still check). Record names only after verifying.
- **Function `name_source`:** `re`/`ihhook`/`lua` verified; `inferred*` rule-based [I]; `vframework` = V_F AddressSet; `sahelan_inventory` = proposal. Roles are a search aid, not proof.
- **Docs:** `[V]`/`[I]`/`[?]`/`[x]` tags; research docs rank first; wiki = `(wiki)`.
- **FoxRe** (`Community\FoxReWiki`, `FoxRe\`): another agent's wiki; several claims wrong. Read `docs\FOXRE_REVIEW.md` before reusing.
- Lua = vanilla 1.0.15.4 only (733 files; duplicates across packs inflate counts).

## 4. Knowledge DB
Derived, rebuildable (~30 s full). Each source has a fingerprint (input path/size/mtime + builder source); `update()` rebuilds only changed sources, re-derives `functions`/`roles` when an upstream source changed, merges FTS, vacuums at >25 % free. Background sync runs at server start; log `logs\knowledge_update.log`.

| Source | Inputs | Tables |
|---|---|---|
| symbols | `symbol_map.tsv`, `inferred_names.tsv`, V_F AddressSet (EN) | `symbols` |
| classes | `xrefs.db` | `classes` |
| commands | `cmd_handlers.tsv`, V_F `GameObjectSendCommand.cpp`, vanilla Lua | `commands`, `vf_commands`, `command_lua` |
| bindings / inventory | `lua_bindings.tsv` / `sahelan_inventory.tsv` | `lua_bindings` / `inventory` |
| enums | `atk_enum.tsv`, `gameobject_type_index.tsv`, `decomp\node_tables_all.tsv` | `enums`, `modules` |
| lua | `vanilla_lua_paths.txt` → `EXTRACTED_DATA\…\Current\` | `lua_files`, `lua_fts`, `lua_api` |
| hashes | strcode TSVs, xrefs hashuse, `text_imm.db`, commands, Lua literals, raw48 scan of `GameBackup` exe | `hashes`, `hash_sites` |
| docs | `..\docs\*.md`, `..\CLAUDE.md`, `..\STATUS.md`, `docs\*.md`, `data\re\structs*\*.md`, wiki | `doc_sections`, `docs_fts` |
| decomp | `data\re\decomp\**\*.c` | `decomp_files`, `decomp_fts` |
| foxre | `Community\FoxReWiki\js\wiki_database.js` | docs kind `foxre` (with verdicts), hashes `foxre_entity` |
| ingest | `ingest\**` + registered paths | `src='ingest'` rows, `ext_rows`, `ext_fts` |

`xrefs.db` (calls, refs, vtables, funcs) is attached read-only as `x`, not copied.
CLI: `python mgsv_unified_server\knowledge\mgsv_knowledge_db.py build [--force] [--only a,b] | status | ingest <path> | q <cat> <query> | explain <system> | inspect <cmd>`.
Ingest formats: TSV `address|addr|va`+name → symbols; `strcode*|hash`+name → hashes (verified, so only checked names); other TSV/TXT → `ingested`; `.md` → docs; `.c` named `<hexva>_name.c` → decomp.

**Sync rules:** after changing research data → `mgsv_update_knowledge_db(mode="sync")`. After RE index changes: `python Tools\fast_xrefs.py build` → `python Tools\static_map.py build` (the first drops static_map tables) → sync.

## 5. Paths (all from `mgsv_paths.py`; Tools import the shim `Tools\mgsv_paths.py`)
| Path | Contents |
|---|---|
| `server\` | the server |
| `knowledge\` | `mgsv_knowledge_db.py` (builder/query/CLI), `systems.py` |
| `data\re\` | `xrefs.db`, `text_imm.db`, `fox2.db` (5.4 GB), `fox2_index.tsv` (2.5 GB, FoxIndex output, never read whole), `symbol_map.tsv`, `strcode_*.tsv`, `cmd_handlers.tsv`, `inferred_names.tsv`, `lua_bindings.tsv`, `sahelan_inventory.tsv`, `atk_enum.tsv`, `gameobject_type_index.tsv`, `decomp\`, `mission_scripts\`, `fox2_xml\`, `structs*\` |
| `data\knowledge\` | `mgsv_knowledge.db` (~210 MB, WAL) |
| `ingest\`, `logs\`, `changes\` | drop folder, update log, change records |
| `docs\FOXRE_REVIEW.md` | FoxRe verdicts |
| `..\docs\` (P.DOCS) | project reference docs |
| `..\Memory\research\` (P.RESEARCH) | probe run logs `<probe>_<run>\` |

`mgsv_paths.res(name)` routes old `Memory\research` names: data names → `data\re`, everything else → RESEARCH.

## 6. Extending
1. Logic in `knowledge\` or the server (`tool_<name>(args)`, add to `TOOLS` + `TOOL_DISPATCH`).
2. Paths via `mgsv_paths`; user paths via `resolve_safe_path()`.
3. New DB source: builder `b_<key>(c)` (deletes its `src` rows, inserts, returns count), register in `SOURCE_INPUTS`, `BUILDERS`, `ORDER` (+ `FUNCTION_DEPS` if it feeds functions), add a query path, document in §4.
4. New explain system → `knowledge\systems.py`.
5. Self-test case, run `--selftest`, update this guide (§2, §8).

## 7. Troubleshooting
| Symptom | Fix |
|---|---|
| `re_decompile` connection refused | `python Tools\ghidra_client.py start` |
| "DB not built" / stale results | `mgsv_update_knowledge_db(mode="sync")`; `mode="status"` |
| `game_send_keys` window not found | `game_status`; `python Tools\mgsv_ctl.py boot` |
| `navmesh_validate` mismatch | run nav2lib rebuild helpers before serialize |
| tool missing in client | restart the Claude session |

## 8. History
- 1.4.0 (2026-10-21): engine oracles `re_emulate`, `engine_verify`, `lua51_run` (`server\oracle_tools.py`); `..\Engine\tests\` (nav2 round-trip verifier + sha256 lock); selftest 31/31 with real assertions (`_oracle_checks`: StrCode64 x5 vs foxhash, refusals, Lua sandbox).
- 1.3.1 (2026-10-19): FoxRe review + ingest (`foxre` source, raw48 hash sites).
- 1.3.0 (2026-10-19): dedicated workspace `mgsv_unified_server\`, RE data moved to `data\re`, `mgsv_paths.py`, knowledge engine (4 `mgsv_*` tools). Undo: `changes\CR-20261019-01_workspace\`.
- 1.2.0 (2026-10-18): `re_closure`, `sahelan_inventory`; 1.1.0: `re_sendcommand`, `lua_search`, `vframework_search`.
- 1.0 (2026-10-17): consolidation of `mgsv-re` + wiki/V_F/navmesh/live/adapters (`Quarantine\ChangeRecords\CR-20261017-01_MCP_Unified\`).
- 2026-10-21: docs moved to `..\docs\`; README/MCP_USAGE/KNOWLEDGE_DB/CHANGELOG merged into this file.

---
<small>Source: `mgsv_unified_server/AI_GUIDE.md` in the project repository &middot; generated 2026-10-22.</small>
