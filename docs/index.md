---
hide:
  - toc
---

<div class="hero" markdown>

# FoxRe

**Reverse engineering *Metal Gear Solid V: The Phantom Pain* and rebuilding its Fox Engine — clean-room, test-gated.**

PC 1.0.15.4 &middot; runtime analysis only &middot; no game files published &middot; every claim backed by a pass/fail test

**5 of 12 milestones passed** &middot; current: **M4 Script host**

</div>

<div class="grid cards" markdown>

-   **[Start here](start/index.md)**

    What the project is and how this site is organised.

-   **[Explanations](explain/index.md)**

    One topic per page in plain language: what it is, why it matters, how the engine does it.

-   **[Modding guides](mods/index.md)**

    What the findings mean for a mod, each with a worked example.

-   **[Reference](engine/index.md)**

    Generated specifications: [engine](engine/index.md) and [file formats](formats/index.md), with confidence tags.

-   **[Project status](status/index.md)**

    Roadmap with milestone gates, numbers and the full session log.

-   **[Library](library/index.md)**

    Sources, tools, test fixtures, live captures, external references.

</div>

## Milestones

| | Milestone | Scope | Status |
|---|---|---|:-:|
| M0 | Foundations | workspace, MCP oracles, hash functions | <span class="status pass">PASS</span> |
| M1 | Data layer | read every file container and the core data formats | <span class="status pass">PASS</span> |
| M2 | Entity & reflection core | fox2 → live typed entity graph | <span class="status pass">PASS</span> |
| M3 | Runtime core | scheduler, messages, GameObjects | <span class="status pass">PASS</span> |
| M4 | Script host | Lua 5.1 + Fox/Tpp API | <span class="status in-progress">IN PROGRESS</span> |
| M5 | Resources & mission load | packs, blocks, async resources, mission start | <span class="status pass">PASS</span> |
| M6 | World | terrain, collision, navigation, routes | <span class="status planned">PLANNED</span> |
| M7 | Animation | clips, motion graphs, rigs | <span class="status planned">PLANNED</span> |
| M8 | Gameplay core | Player, Soldier AI, SendCommand handlers, damage (headless) | <span class="status planned">PLANNED</span> |
| M9 | Gameplay extended | sound, bosses, UI | <span class="status planned">PLANNED</span> |
| M10 | Assets & rendering | renderer and viewer last | <span class="status planned">PLANNED</span> |
| M11 | Playable slice | one free-roam area, player + one AI type | <span class="status planned">PLANNED</span> |

## Verified engine modules

| Module | Language | Specification | State | Gate (on all game files) |
|---|---|---|---|---|
| `core/strcode.py` | Python | docstring | <span class="status pass">PASS</span> | StrCode64 = exe 0x141A09AC0 (`re_emulate`, incl. > 64-byte strings) |
| `core/typedb.py` | Python | [`docs/engine/Reflection.md`](engine/reflection.md) | <span class="status pass">PASS</span> | game registry dump == all DataSets (3,372/3,372 props) |
| `core/entities.py` | Python | [`docs/engine/Entities.md`](engine/entities.md) | <span class="status pass">PASS</span> | s10151: 8,669 entities typed, all refs resolved/categorised; live: 17/17 f30010 identifier targets match the game |
| `core/pathcode.py` | Python | [`docs/formats/QAR.md`](formats/qar.md) | <span class="status pass">PASS</span> | 111,394 QAR entry hashes matched by names |
| `formats/qar.py` | Python | [`docs/formats/QAR.md`](formats/qar.md) | <span class="status pass">PASS</span> | 134,241 entries MD5-verified, headers/tables re-encode exactly |
| `formats/fpk.py` | Python | [`docs/formats/FPK.md`](formats/fpk.md) | <span class="status pass">PASS</span> | 16,354/16,354 packages byte-identical, 732 Lua decode + compile |
| `formats/fox2.py` | Python | [`docs/formats/FOX2.md`](formats/fox2.md) | <span class="status pass">PASS</span> | 44,994/44,994 DataSets byte-identical |
| `formats/frt.py` | Python | [`docs/formats/FRT.md`](formats/frt.md) | <span class="status pass">PASS</span> | 307/307 route sets byte-identical |
| `formats/nav2.py` | Python (+numpy) | [`docs/NAVMESH.md`](formats/nav2.md) | <span class="status pass">PASS</span> | 840/840 navmeshes byte-identical |
| `runtime/` (gameobjects, scheduler, messages) | Python | [`docs/engine/Scheduler.md`](engine/scheduler.md), `Messages.md` | <span class="status pass">PASS</span> | live FoxTrace fixture: every updater-vector change and 43-message boot sequence reproduced (`test_m3_runtime.py`) |
| `script/` (host, vfs, foxmath.lua) | Python + Lua 5.1 (lupa) | [`docs/engine/ScriptHost.md`](engine/script-host.md) | <span class="status in-progress">IN PROGRESS</span> | boot runs the game's own init.lua + Tpp/start.lua with no error, 108 chunks in the live order up to the mission load (`test_m4_script_host.py`); API: 399 libraries from the binding map, 15 natives, 328 stubs touched |
| `resources/` (loader, blocks, fstb) + pack mounts in `script/vfs.py` | Python | [`docs/engine/Resources.md`](engine/resources.md) | <span class="status in-progress">IN PROGRESS</span> | location/mission loading driven by the game's own Lua package lists, script blocks (8 slots), soldier common-motion block: 49/49 live chunks from live chunk 112 to the end of the boot (init -> title 40010 -> f30010 -> quest / reinforce / animal blocks; UI tables still excluded), block events and script-block loads match (`test_m5_mission_load.py`, `test_m5_script_blocks.py`) |

## Latest sessions

- 2026-10-24: **Mod checkpoint rework 1 Foundation PASS**: overlay `vsahelan` (deploy/restore round trip MATCH), merged module `InfSahelanPilot.lua` (one gate owner, edge release), build on `Engine\formats` (t2b byte-identical), bench 13/13.
- 2026-10-24: **Mod checkpoint rework session 1**: Luc's 3.1 run read (pilot works in game; release-key bug; gatling hit no soldier; 0 player damage), mod-baseline + t2b (MATCH 98 files), `vsahelan.ps1 restore` fix; `docs\OPEN_QUESTIONS.md` (13 answered/narrowed, capture `trace_oq_callers`); rework plan `SAHELAN_FEASIBILITY.md` §6.
- 2026-10-24: **Mod checkpoint 3.1 implemented offline** (`SahelanControl.GetKeys()` / `IsKeyDown` in V_Sahelan r7b keys, IH module `InfVSahelanPilot.lua`, Numpad `*` toggle; bench 7/7; build `B5C2A5A9…`, not deployed).
- 2026-10-24: **Mod checkpoint 3.1 prep + 3.5 tail** (keyboard → Lua map [V live] `m_pad_20261024_1555`: unbound keys invisible, toggle Numpad `*` via the DLL; V_Sahelan startup `CheckAddresses()` built, 42 checked prologues in the ledger).
- 2026-10-24: **Mod checkpoint 3.5 + 3.6 PASS** (V_Sahelan address audit via claims source `v_sahelan`: 59 addresses, 35 V / 36 W / 0 x; offline mod bench `test_mod_sahelan_bench.py`); 3.4 decode: `ScriptBlock.Load(id, "")` = unload [V static].

[Full session log](status/log.md)
