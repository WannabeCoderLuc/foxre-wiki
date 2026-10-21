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

## MCP / tool upkeep backlog (audit 2026-10-22, do before M4 research)
Found by what had to be done by hand during M3 (≈40 shell calls, 6 failed MCP calls, 4 one-off scripts).
**Fix**

1. `game_status`: list every file in `plugins\` and `mod\modules\` (hash + build tag) and diff against a baseline manifest (`Tools\game_baseline.json`); today it only checks SahelanControl.dll + V_FrameWork.dll, so a leftover `FoxTrace.dll` or stray module would go unnoticed.
2. `re_class`: exact-address mode; `re_class 0x1421AF098` snapped to the run start 0x1421AF088 and showed the wrong slots.
3. Parameter aliases on every `re_*` tool (`va`, `address`, `va_or_name`, `query`, …) — 6 calls failed on name guesses.
4. `re_field_access`: default region = whole exe (still "sahelan").
5. `engine_verify(quick=true)`: pytest marker `slow` on all-game-file verifiers → ~30 s inner loop (full run 9.5 min).
**Add**

6. `game_session(boot|stop)` → wraps `mgsv_ctl.py boot/stop` (now Bash only).
7. `game_plugin(deploy|restore, name, profile)` with the baseline manifest: restore puts back every changed file and archives logs to `Memory\research\<name>_<time>\` (replaces ~25 per-probe `.ps1` scripts).
8. `trace_capture(config, seconds, runs)`: FoxTrace deploy → boot → wait → stop → restore → compare runs → summary (M3 by hand; M4 needs the same for Lua API calls).
9. `re_bytes(va, n)` / exact vtable slot dump from the pristine exe (replaces ad-hoc `lief` reads).
10. `re_hash`: GameObject type-index names; one shared name resolver (StrCode32 dictionary) importable by tools (`distill_fixture.py` re-implements it).
**Generalise**

11. FoxTrace 2: hook list from a config file (VA, arg layout, what to log) instead of hard-coded targets; `compare_runs.py` + `distill_fixture.py` fold into `trace_capture`.
**Retired 2026-10-22:** `build_foxre_wiki.py`, `generate_foxre_logos.py`, `generate_foxre_parody.py`, `build_perfect_foxre_logo.py`, `sync_wiki_fork.py`, `reorg_2026_10_17.py`, `build_wiki.py` → `Quarantine\Cleanup_2026-10-22\`.

## Game boot profiles (recommendation 2026-10-22)
Installed now (SnakeBite `snakebite.xml`): IHHook r25, Infinite Heaven r267, V Framework 1.6.0.1, **Sahelanthropus Puppet Pilot** (data mod, `a_chunk7.dat`); `plugins\`: SahelanControl r5c + V_FrameWork; `mod\modules\`: 2 active + 4 inert Sahelan modules. Mod track is parked, so this is more than engine work needs.
**Best option — "engine-clean" profile for every ground-truth capture:**

- Keep IHHook + Infinite Heaven only (plugin loader + Lua pipe for `game_pipe_lua` / `mgsv_ctl boot`).
- `plugins\`: only the trace DLL of the run (FoxTrace); move SahelanControl.dll + V_FrameWork.dll aside (V_F hooks Lua/native entry points that M4 will trace).
- `mod\modules\`: stock IH only (move the 6 `Inf*Sahelan*/Probe/Noise` modules aside).
- Game data: uninstall **Sahelanthropus Puppet Pilot** and V Framework in SnakeBite (Luc) so the live game matches the pristine `GameBackup` data the engine reads; fixtures then describe vanilla 1.0.15.4.
- Switching is done by `game_plugin(profile=engine-clean|mod-baseline)` (backlog 7) from manifests; "mod-baseline" = today's setup, restored when the mod track resumes.
**Newer versions:** IH r267 / IHHook r25 / V_F 1.6.0.1 are the newest we have (Sept–Oct 2026); check Nexus for later IH/IHHook builds before M4 [?] — IHHook updates may move hook addresses FoxTrace chains onto.
**Boot speed:** ~75 s cold boot to free roam; IH options for skipping logos/title [?] (check IH r267 docs) would shorten every capture.

## Not installed (needs a purchase/licence or was rejected)
See the links in the 2026-10-21 report ([`docs\LOG.md`](../status/log.md)); skipped: paid tools (IDA Pro, 010 Editor), FMDL Studio v2 (Unity plugin, needs a Unity account; our own fmdl codec + Blender instead); rejected: Sogen for the game exe (running Denuvo under an emulator is off-limits), REA (repo gone, closed zip), decomp.wtf (archived; console-only).

---
<small>Source: `docs/TOOLING.md` in the project repository &middot; generated 2026-10-22.</small>
