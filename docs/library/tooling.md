# Installed tools

## Lessons from github.com/yibie/awesome-rea (AI-assisted RE projects)
The list's one rule: a project counts only if correctness is a **machine-decidable PASS/FAIL gate** set before agents iterate. What the strongest entries do:

- **momo5502, "500+ billion tokens"** (PC FPS, MSVC): byte-matching oracle (compile with original compiler → compare function bytes vs EXE, relocations checked by symbol+offset) → 99 % functions, 83 % byte-exact. CI re-verifies; the verifier script is hash-locked so agents can't edit it; inline asm banned. Context compaction at 42 % instead of 90 % helped more than model upgrades; hourly instruction re-read against drift; reviewer agents were useless without an objective gate; discard bad code rather than salvage it. Tooling: ida-mcp, Sogen emulator.
- **DecompPipeline** (Ghidra + emulator oracle): each function judged PASS/FAIL by running original vs reimplementation in an emulator; every harness is **stamped with its oracle input** so stale harnesses can't pass; locked-down `claude -p` workers; files ≤ 400 lines.
- **decomp-compat-kit**: an **independent** verifier (stock toolchain, outside the agents' build) that classifies every mismatch; only "unexplained" needs a human. A hash says nothing about types/names — meaning must be checked separately.
- Post-mortems: progress climbs fast then stalls (~25 % → 58 %); ~5 % still needs an expert; "slopcomps" (unverified AI ports) are the community's red line. decomp.wtf was archived after community pushback.

**Applied to us** (clean-room engine, not matching decompilation — mgsvtpp has 141k functions, Denuvo, and publishing derived code is legally fraught):

1. Every format: byte-identical round trip on **all** game files (`fox-format` skill).
2. Every pure algorithm (hashes, decompression, quantisation, math): **emulator oracle** — run the original function from `GameBackup` `.xtext` in unicorn with test inputs, compare to our implementation. Never emulate code that reaches `.xdata`/`.ecode` (Denuvo).
3. Every behaviour: live fixtures (`fox-ground-truth`), stamped with the build + capture inputs.
4. Verifiers live outside `Engine\` and are hash-locked in CI; tests must stay green.

## Installed (2026-10-21)
| Tool | How | Use |
|---|---|---|
| Ghidra 12.1.4 + `Tools\ghidra_client.py` server, **pyghidra 3.1** | existing / pip | decompile, headless scripting from Python |
| MSVC 2022 (cl 14.44), .NET 9, Python 3.13, Git | existing | builds |
| capstone, pefile, **lief 1.0**, **unicorn 2.1.4**, **keystone 0.9.2** | pip | disassemble, parse PE, emulate single functions, assemble test stubs |
| **kaitaistruct**, **construct** + Kaitai Struct compiler | pip / winget | declarative format specs → parsers |
| **pytest** | pip | engine test runner |
| **lupa 2.8** (`lupa.lua51` = Lua 5.1, also LuaJIT) | pip | run game Lua 5.1 in Python; engine script host prototype |
| **uv**, **cmake 4.4**, **ninja 1.13** | pip | Python tooling (ida-mcp needs uv), C++ engine builds |
| **gh** | winget | GitHub CLI (repo, CI, issues) |
| **ImHex** | winget | hex editor with pattern language |
| **RenderDoc 1.46** | winget (signed by Baldur Karlsson) | D3D11 frame capture: shaders, draws, render targets. Injecting into mgsvtpp may clash with Denuvo/V_F hooks: test with plugins off |
| **vcpkg** (`C:\Tools\vcpkg`) | git + bootstrap (signed by Microsoft) | C++ libraries for the engine (e.g. `vcpkg install imgui`) |
| **Blender** | winget | view decoded models/animations |
| Cheat Engine | existing | memory inspection of the running game (single player) |
| MCP: mgsv-unified, atomizer, websift | existing | see [`mgsv_unified_server\AI_GUIDE.md`](mcp-server.md) |

## MCP / tool upkeep (audit 2026-10-22) — PASS, MCP 1.5.0
Found by what had to be done by hand during M3 (≈40 shell calls, 6 failed MCP calls, 4 one-off scripts). All 11 items done 2026-10-22; usage in [`mgsv_unified_server\AI_GUIDE.md`](mcp-server.md).

| # | Item | Done as |
|---|---|---|
| 1 | `game_status` saw only 2 DLLs | lists every file of `plugins\` + `mod\modules\` (sha1 + tag) and diffs it against the profiles in `Tools\game_baseline.json` |
| 2 | `re_class 0x1421AF098` snapped to the run start | an address inside a vtable run is dumped from exactly that address (pristine exe); `exact=true` forces it |
| 3 | 6 calls failed on parameter names | aliases on every tool (`va`/`address`/`query`/… → main parameter, tool-specific ones); unknown names list the accepted ones |
| 4 | `re_field_access` default "sahelan" | default `all`; `static_map.py build` now indexes all of `.xtext` (1,284,530 operands, 88 s; ranges in `meta.fields_ranges`), query < 0.1 s |
| 5 | engine_verify 9.5 min inner loop | `quick=true` → `-m "not slow"`; marker set in `Engine\tests\conftest.py` for the fox2/qar/fpk round-trips |
| 6 | boot/stop only via Bash | `game_session(boot\|stop\|status)` (`mgsv_ctl.boot` / new `mgsv_ctl.stop`) |
| 7 | ~25 per-probe `.ps1` deploy/restore scripts | `game_plugin(status\|apply\|deploy\|restore)` = `Tools\game_profiles.py`: profiles, overlays, content-addressed stash `Backups\game_profiles\stash\<sha1>\` (nothing deleted), logs archived to `Memory\research\<name>_<time>\`. Round trip mod-baseline → engine-clean → +FoxTrace → mod-baseline tested on the live install |
| 8 | M3 capture by hand | `trace_capture(run\|status\|compare)` = `Tools\trace_capture.py` (background; always ends on mod-baseline) |
| 9 | ad-hoc `lief` reads | `re_bytes(va, n, disasm)` |
| 10 | type names / resolver re-implemented | `re_hash` `type:<n>` / `id:<goid>` / type names; shared `Tools\foxnames.py` (distill_fixture uses it; same names on all 43 M3 messages) |
| 11 | FoxTrace hard-coded | FoxTrace 2: `plugins\FoxTrace.cfg` (`builtin m3`, `hook <name> <va> <args i,f,d,s,L> [max=N]`, `luaofs`, `heartbeat`, `maxlines`); generated register-saving entry stub, checked off-game by `build.ps1 -Test` (int/float/double/string/stack args, PASS). compare_runs.py → `trace_capture compare` (same verdict on the M3 runs); foxtrace.ps1 → `game_plugin` (both in `Quarantine\ToolUpkeep_2026-10-22\`) |

FoxTrace 2 `L` decoding [V] static: `lua_gettop` 0x141A112E0 = (L+0x10 − L+0x18) >> 4; TValue 16 B, `tt` at +8, stock type numbers; `lua_tolstring` 0x141A12150 returns `*(TString+0x18)` — a **pointer** to the chars (Fox change, stock Lua stores them inline), length at TString+0x10; Udata payload +0x28 (`lua_touserdata` 0x141A122C0). Open: no live FoxTrace 2 run yet.
**Retired 2026-10-22:** `build_foxre_wiki.py`, `generate_foxre_logos.py`, `generate_foxre_parody.py`, `build_perfect_foxre_logo.py`, `sync_wiki_fork.py`, `reorg_2026_10_17.py`, `build_wiki.py` → `Quarantine\Cleanup_2026-10-22\`.

## Static exe scans: `Tools\xscan.py` (2026-11-04)
One tested CLI for the scans that were rewritten by hand in M9 (one of them silently read nothing because it looked for `.rdata`). Reads `GameBackup\MGS_TPP\mgsvtpp.exe` through `fast_xrefs.PE` and `xrefs.db`; every hit is checked against a linear disassembly of its function. Tests: `python -m pytest Tools\test_xscan.py -q` (~10 s, known answers below).

| Command | Answers | Known answer (test) |
|---|---|---|
| `callarg <slot> [--arg r8=0x3b] [--range lo-hi]` | call sites of `call [reg+slot]` with rcx/rdx/r8/r9/xmm0-3 as set in the 12 instructions before (window stops at an earlier call); `--arg` filters, prints where each was set | `callarg 0x30 --arg r8=0x3b` → site 0x140D6D653, r8 set at 0x140D6D640 |
| `imm <value> [--range] [--live]` | every instruction using the immediate (`text_imm.db`; `--live` or an unindexed value disassembles the range) | `imm 0x3b` → `mov r8d, 0x3b` at 0x140D6D640 |
| `bits <disp> <mask> [--range]` | or/and/xor/test/bt/bts/btr/btc with an immediate on `[reg+disp]`: set / clear / toggle / test; byte/word sub-accesses folded in, a complement mask is flipped | `bits 4 0x80` → setter `or dword ptr [r8+4], 0x80` at 0x140D6A032 |
| `const <f>[,<f>...] [--f64] [--top N]` | data addresses of the float32 values, then the functions reading them rip-relative (incl. 16-byte vector loads), ranked by how many of the values each reads | `const 0.8,2.75,4.0` → 0x14139D600 first (3/3) |

Gotchas behind it:

- **Section names are Denuvo's:** data is in `.edata` / `.data2` (and `.text`, `.didata`); there is no `.rdata`; code is `.xtext`. Pick sections by characteristics (initialized data, not executable, not discardable), never by name (`xscan.data_sections`).
- **`xrefs.db refs` before 2026-11-04 had no SSE or non-REX rip-relative operands:** `fast_xrefs.py` matched only `REX + 8B/89/8D/3B/39/63`, so `movss xmm0, [rip+x]` (`f3 0f 10 05`) and `mov eax, [rip+x]` were missing (212,056 refs). Now `fast_xrefs.rip_refs`: `[66|F2|F3] [REX] op modrm(rip) disp32 [imm]` for GPR ops (incl. imm forms) and `0F xx` SSE/movzx/setcc/cmov/bt ops, each confirmed with capstone → 379,999 refs; new column `refs.op` = prefix+opcode (0xf30f10 movss load, 0x8b mov, 0x8d lea). Not covered: VEX/AVX encodings, `0F 38`/`0F 3A` maps, `F6/F7` (test imm), `x87`.
- **Code with no `funcs` row** (no `.pdata`, < 3 direct calls, e.g. the unrealized speed function 0x14139D600): `refs.func` is 0; `xscan` guesses the start (`Exe.guess_func`: last 16-aligned address after ret/int3/nop padding that disassembles onto the site) and prints "(guessed start)".
- **`text_imm.db` small values:** kind `s` (new) = `mov`/`cmp` immediates 2..0xFF (`mov r8d, 0x3b` was missing: `w` starts at 0x100). 0 and 1 are not indexed; `imm 0`/`imm 1` and other mnemonics (`add`, `and`, ... below 0x100) scan live.
- `fast_xrefs.py build` / `text_scan.py build` rebuild their tables in place when the MCP server holds the DB open (Windows can't delete it).

## Game boot profiles
Manifest `Tools\game_baseline.json` (switch with `game_plugin`; `game_status` shows which one matches):

- **engine-clean** (every ground-truth capture): only the 92 files SnakeBite lists for IHHook r25 + Infinite Heaven r267 (plugin loader + Lua pipe). Aside: `SahelanControl.dll`, `V_FrameWork.dll`, the 5 V_F Lua modules (`V_*.lua`), `InfVSahelanNoise.lua`, `InfVSauceNoise.lua`. Trace DLLs come on top as overlays (`foxtrace`).
- **mod-baseline** (restore target, CLAUDE.md): the 101 files of 2026-10-22 after Luc's Puppet Pilot uninstall: IHHook + IH + V Framework 1.6.0.1 + SahelanControl r5c + the two inert Sahelan modules.
- Still open for Luc: uninstall V Framework in SnakeBite so the game *data* is vanilla too (the profile only removes its DLL + Lua modules). After that, re-snapshot mod-baseline (`python Tools\game_profiles.py snapshot mod-baseline`) or keep V_F files in the stash for the mod track.
**Nexus check 2026-10-22 (report only, nothing installed):** IHHook r25 (22 Sep 2026) and Infinite Heaven r267 (21 Sep 2026) are the newest uploads; no newer builds. IH r267 has the option **Skip startup logos** (`Ivars.skipLogos`, IH menu "Skip startup logos": konami/kjp/fox/nvidia logos) and **Start offline** (`Ivars.startOffline`, skips the online connect); both off now (not in `ih_save.lua`). No IH option skips the title screen: CONTINUE stays a keypress (`mgsv_ctl boot` already sends it). Enabling both would cut the boot; Luc's call (set in the IH menu, or `ih_save.lua` with the game closed + backup).

## Not installed (needs a purchase/licence or was rejected)
See the links in the 2026-10-21 report ([`docs\LOG.md`](../status/log.md)); skipped: paid tools (IDA Pro, 010 Editor), FMDL Studio v2 (Unity plugin, needs a Unity account; our own fmdl codec + Blender instead); rejected: Sogen for the game exe (running Denuvo under an emulator is off-limits), REA (repo gone, closed zip), decomp.wtf (archived; console-only).

## Dev-build symbol DB (`re_devmap`, 2026-11-04)
`GeminiWork\decomp\mgsv.db` (808 MB SQLite) maps the 2015 dev build `Tpp_main_win64.exe` (build 2, 2015-08-03) onto our retail exe (build 1): 135k retail functions with name, `source` confidence, proto, class, obj/module, the matched dev function (`retail.dev`) and its decompile (`decomp`, key `dev`), vtables (`vtables` + `globals` kind `vftable`), a `verify` table with the match evidence, and FTS4 over the dev code (`fts_code`). In the M9 session it named the CP radio / member-role system and the unrealized speed function in minutes where hand RE had stalled.

- **Access:** MCP `re_devmap` (`mgsv_unified_server\server\devmap.py`). Path `mgsv_paths.DEVMAP_DB` (override `MGSV_DEVMAP_DB`), opened `mode=ro`. Modes: `va` (hex, default) = dossier: name, source, tag, proto/class, correlators, byte signature, `verify` evidence, vtable slots, dev decompile (`lines` / `start_line`); `name` = retail functions whose dev name contains the text (EXACT first); `vtable` = slots of a class (every `Class::vftable{for Base}`) or one vftable VA; `code` = FTS4 query over the dev decompiles → dev function, file, retail mapping. Shell: `python Tools\mcpcall.py re_devmap '{"query":"0x140D5AAA0"}'`.
- **Build guard:** every open compares `builds.sha256` (id 1) with sha256 of `GameBackup\MGS_TPP\mgsvtpp.exe` (`085c2f82…bb45`); mismatch or a missing file refuses the open (`DevmapRefused`). `re_decompile` / `re_xrefs` then print `devmap not applied: …` and stay usable.
- **In other tools:** `re_decompile` appends `/*[dev] Name*/` after `FUN_` addresses that `symbol_map.tsv` leaves unnamed and adds a `// devmap:` header line for the function itself; `re_xrefs` appends ` [dev] Name` after unnamed function starts and vftables. Only `source = EXACT` (vftables: `globals.method = vt-exact`) is written `[dev]`; AUTO / REF / LUA / THUNK and `vt-implied` / `ref` vftables are written `[hint <source>] Name`; DEFAULT / ANALYSIS give nothing. Counts in build 1: EXACT 34,549 · AUTO 15,918 · REF 13,502 · DEFAULT 68,785.
- **Evidence rule:** a dev name is **[I]** until the retail body has been read (it describes the 2015 build; retail may differ or fold). A name may go into `symbol_map.tsv` with source `devmap` only when it is **EXACT and** the retail body was read and its instructions match the dev decompile (same calls, field offsets, constants); then the claim is [V] for that body. AUTO / REF names are leads only: confirm by reading the retail body before using or recording them.
- **Known trap (probably identical-code folding, not yet checked):** a tiny shared body can be EXACT for an unrelated function, e.g. `CommandPost2Impl` vftable `{for fox::Quark}` slot 4 (0x1400fe390) reads `[dev] fox::fs::GameDataInstaller::CancelPermit`. Take the slot's class from the vftable, not from the folded name, and read the body.
- **Selftest:** `_devmap_checks` (in `--selftest`): build guard accepts the retail exe and refuses a foreign one; the hand-confirmed EXACT pairs of 2026-11-04 come back unchanged (0x140D69FB0 `AlertAiImpl::CheckActiveMember`, 0x140D63550 `CommandPost2Impl::SetMemberRole_`, 0x14139D600 `UnrealBasicAction2Impl::GetMoveVelocityForUnreal`, 0x140D5AAA0 `CommandPost2Impl::DoRequestRadio`) with dev decompile and `verify` rows; AUTO is labelled `[hint AUTO]`, never `[dev]`; annotation leaves call-site addresses alone.

---
<small>Source: `docs/TOOLING.md` in the project repository &middot; generated 2026-11-04.</small>
