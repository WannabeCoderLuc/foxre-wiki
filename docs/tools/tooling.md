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

## Game boot profiles
Manifest `Tools\game_baseline.json` (switch with `game_plugin`; `game_status` shows which one matches):

- **engine-clean** (every ground-truth capture): only the 92 files SnakeBite lists for IHHook r25 + Infinite Heaven r267 (plugin loader + Lua pipe). Aside: `SahelanControl.dll`, `V_FrameWork.dll`, the 5 V_F Lua modules (`V_*.lua`), `InfVSahelanNoise.lua`, `InfVSauceNoise.lua`. Trace DLLs come on top as overlays (`foxtrace`).
- **mod-baseline** (restore target, CLAUDE.md): the 101 files of 2026-10-22 after Luc's Puppet Pilot uninstall: IHHook + IH + V Framework 1.6.0.1 + SahelanControl r5c + the two inert Sahelan modules.
- Still open for Luc: uninstall V Framework in SnakeBite so the game *data* is vanilla too (the profile only removes its DLL + Lua modules). After that, re-snapshot mod-baseline (`python Tools\game_profiles.py snapshot mod-baseline`) or keep V_F files in the stash for the mod track.
**Nexus check 2026-10-22 (report only, nothing installed):** IHHook r25 (22 Sep 2026) and Infinite Heaven r267 (21 Sep 2026) are the newest uploads; no newer builds. IH r267 has the option **Skip startup logos** (`Ivars.skipLogos`, IH menu "Skip startup logos": konami/kjp/fox/nvidia logos) and **Start offline** (`Ivars.startOffline`, skips the online connect); both off now (not in `ih_save.lua`). No IH option skips the title screen: CONTINUE stays a keypress (`mgsv_ctl boot` already sends it). Enabling both would cut the boot; Luc's call (set in the IH menu, or `ih_save.lua` with the game closed + backup).

## Not installed (needs a purchase/licence or was rejected)
See the links in the 2026-10-21 report ([`docs\LOG.md`](../status/log.md)); skipped: paid tools (IDA Pro, 010 Editor), FMDL Studio v2 (Unity plugin, needs a Unity account; our own fmdl codec + Blender instead); rejected: Sogen for the game exe (running Denuvo under an emulator is off-limits), REA (repo gone, closed zip), decomp.wtf (archived; console-only).

---
<small>Source: `docs/TOOLING.md` in the project repository &middot; generated 2026-10-22.</small>
