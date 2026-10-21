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

## Not installed (needs a purchase/licence or was rejected)
See the links in the 2026-10-21 report ([`docs\LOG.md`](../status/log.md)); skipped: paid tools (IDA Pro, 010 Editor), FMDL Studio v2 (Unity plugin, needs a Unity account; our own fmdl codec + Blender instead); rejected: Sogen for the game exe (running Denuvo under an emulator is off-limits), REA (repo gone, closed zip), decomp.wtf (archived; console-only).

---
<small>Source: `docs/TOOLING.md` in the project repository &middot; generated 2026-10-22.</small>
