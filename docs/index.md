---
hide:
  - toc
---

<div class="hero" markdown>

# FoxRe

**Reverse engineering *Metal Gear Solid V: The Phantom Pain* and rebuilding its Fox Engine — clean-room, test-gated.**

PC 1.0.15.4 &middot; runtime analysis only &middot; no game files published &middot; every claim backed by a pass/fail test

**6 of 15 milestones passed** &middot; current: ****

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
| M4 | Script host | Lua 5.1 + Fox/Tpp API | <span class="status pass">PASS</span> |
| M5 | Resources & mission load | packs, blocks, async resources, mission start | <span class="status pass">PASS</span> |
| M6 | World streaming & locators [NEXT] — stage blocks, location loader, locators | stage blocks, location loader, locators | <span class="status planned">PLANNED</span> |
| M7 | Terrain & collision formats | `.htre`/`.tre2`, `.geom` | <span class="status planned">PLANNED</span> |
| M8 | Navigation & routes | nav2 runtime, route following | <span class="status planned">PLANNED</span> |
| M9 | Gameplay core | Soldier AI, CP / notice, damage, SendCommand handlers (headless) | <span class="status planned">PLANNED</span> |
| M10 | Asset formats | textures, models, rigs, fova, parts, language | <span class="status planned">PLANNED</span> |
| M11 | Animation | clips, motion graphs, motion events | <span class="status planned">PLANNED</span> |
| M12 | Gameplay extended | sound, bosses, UI | <span class="status planned">PLANNED</span> |
| M13 | Rendering & viewer | renderer last | <span class="status planned">PLANNED</span> |
| M14 | Playable slice | one free-roam area, player + one AI type | <span class="status planned">PLANNED</span> |

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

- 2026-10-29: **M4 Script host PASS** (Luc accepted gates a + b with the documented differences).
- 2026-10-29: **Roadmap re-cut** (Luc): M6+ ordered by dependency and feasibility (M6 streaming & locators, M7 terrain/collision, M8 navigation, M9 gameplay core, M10 asset formats, M11 animation, M12 gameplay extended, M13 rendering, M14 slice); gap map, open questions, skills, site updated.
- 2026-10-29: **M4 gate b (call-log comparison)**: FoxTrace table results (Lua Table layout [V static]); capture f30020 (574 hooks); host follows the live save (title 40020 → f30020), free roam with delivery to `Seq_Game_FreePlay`; call log 548 both / 517 same args / order 0.947, one-sided functions all explained; replay fixture 723 natives (4 captures); `test_m4_gate_b.py`; quick suite 65/65.
- 2026-10-28: **Sahelanthropus mod track retired** (Luc): removed from goals, Next, ROADMAP (Mod checkpoint), CLAUDE.md and the skills; SAHELAN / PROBES / BATTLEFIELD docs kept as RE evidence only.
- 2026-10-28: **M4 gate a part 3 (login, DLC, pre-title)**: Konami login decoded (0x1407D74A0 / 0x1407DEE70 / 0x14091C470 / 0x1407D50A0; live popups = `system_3200_all` ×2, `system_3201_all`), pre-title UI 0x14085C8C0 → Lua `TppVarInit.StartTitle` [V static]; `Engine\runtime\online.py`; host = 24 live transitions, loads title 40010 itself; m5 58/58 hand-driven only from CONTINUE; quick suite 62/62.

[Full session log](status/log.md)
