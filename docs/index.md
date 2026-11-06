---
hide:
  - toc
---

<div class="hero" markdown>

# FoxRe

**Reverse engineering *Metal Gear Solid V: The Phantom Pain* and rebuilding its Fox Engine — clean-room, test-gated.**

PC 1.0.15.4 &middot; runtime analysis only &middot; no game files published &middot; every claim backed by a pass/fail test

**8 of 25 milestones passed** &middot; current: ****

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
| M6 | World streaming & locators | stage blocks, location loader, locators | <span class="status pass">PASS</span> |
| M7 | Terrain & collision formats [PASS 2026-10-29] — `.htre`/`.tre2`, `.geom` | `.htre`/`.tre2`, `.geom` | <span class="status planned">PLANNED</span> |
| M8 | Navigation & routes | nav2 runtime, path queries (Luc, 2026-11-01) | <span class="status pass">PASS</span> |
| M9 | Gameplay core [PASS, Luc 2026-11-04] — Soldier AI, CP phases and notice, route following (headless) | Soldier AI, CP phases and notice, route following (headless) | <span class="status planned">PLANNED</span> |
| M10 | Mod API core [PASS, Luc 2026-11-05: G1-G7, C1-C8 PASS (C3 N/A)] — registries, manifest, loader, hooks (headless) | registries, manifest, loader, hooks (headless) | <span class="status planned">PLANNED</span> |
| M11 | Asset formats | textures, models, rigs, fova, parts, language, sound containers | <span class="status planned">PLANNED</span> |
| M12 | Sound & UI logic | sound events, music states, menus, iDroid, HUD (headless) | <span class="status planned">PLANNED</span> |
| M13 | Open world complete | both maps, every block level, clock, weather, random numbers (headless) | <span class="status planned">PLANNED</span> |
| M14 | Collision & physics | shape trees, queries, character controller, rigid bodies | <span class="status planned">PLANNED</span> |
| M15 | Combat & equipment | weapons, ballistics, hits, damage, CQC logic, items, Fulton (headless) | <span class="status planned">PLANNED</span> |
| M16 | Animation | clips, motion graphs, motion events, root motion, ragdoll | <span class="status planned">PLANNED</span> |
| M17 | Headless slice | one free-roam area, player + one AI type, input replay, zero recorded natives | <span class="status planned">PLANNED</span> |
| M18 | Full cast | every soldier type, animals, buddies, heli, vehicles, bosses | <span class="status planned">PLANNED</span> |
| M19 | Missions & progression | missions, objectives, demos, Mother Base, saves | <span class="status planned">PLANNED</span> |
| M20 | Rendering | reference renderer, renderer last | <span class="status planned">PLANNED</span> |
| M21 | Audio output | Wwise-compatible playback | <span class="status planned">PLANNED</span> |
| M22 | Playable game | rendering + audio + input on the verified headless game | <span class="status planned">PLANNED</span> |
| M23 | Standalone runtime | C++ frame loop, packaging | <span class="status planned">PLANNED</span> |
| M24 | Mod platform 1.0 | API freeze, asset packs, native plugins, mod manager | <span class="status planned">PLANNED</span> |

## Verified engine modules

| Module | Language | Specification | State | Gate (on all game files) |
|---|---|---|---|---|
| `mods/` (registry, loader, vanilla) | Python | [`docs/engine/ModAPI.md`](engine/mod-api.md) | <span class="status pass">PASS</span> | Mod API core (M10): registries for GameObject types, commands, messages, updaters, AI tables, parameters, resource loaders, reflection classes, Lua libraries, natives; manifest + load order; vanilla registered through the same `ModContext`; ScriptHost installs Lua libraries and natives only from its registry. G1: every dump equals its source table (`test_m10_registry.py`). |
| `native/` (`_foxnative`: heightfield, navigation) | C++17 (pybind11, MSVC `/fp:strict`) | [`docs/engine/Native.md`](engine/native.md) | PASS (M10 C7) | C++ copies of `HeightField.sample` and `NavWorld.find_path`, bit-identical to the Python reference on 948 nav jobs, 410 requests and 200,036 height points, about 19x (nav) / 300x (batched heights) faster (`test_cpp_equiv.py`, M10 C7); default backend when built (`python Tools/build_native.py`), `ENGINE_BACKEND=py` forces Python. |
| `world/realize.py` | Python | [`docs/engine/SoldierAI.md`](engine/soldier-ai.md) | <span class="status in-progress">IN PROGRESS</span> | Soldier realize selection (far mode): budget inside the stage window, 32 / 28 m inset. 159 of 181 live lists equal, the rest within sample age (`test_m9_soldier.py`). |
| `core/strcode.py` | Python | docstring | <span class="status pass">PASS</span> | StrCode64 = exe 0x141A09AC0 (`re_emulate`, incl. > 64-byte strings) |
| `core/typedb.py` | Python | [`docs/engine/Reflection.md`](engine/reflection.md) | <span class="status pass">PASS</span> | game registry dump == all DataSets (3,372/3,372 props) |
| `core/entities.py` | Python | [`docs/engine/Entities.md`](engine/entities.md) | <span class="status pass">PASS</span> | s10151: 8,669 entities typed, all refs resolved/categorised; live: 17/17 f30010 identifier targets match the game |
| `core/pathcode.py` | Python | [`docs/formats/QAR.md`](formats/qar.md) | <span class="status pass">PASS</span> | 111,394 QAR entry hashes matched by names |
| `formats/qar.py` | Python | [`docs/formats/QAR.md`](formats/qar.md) | <span class="status pass">PASS</span> | 134,241 entries MD5-verified, headers/tables re-encode exactly |
| `formats/fpk.py` | Python | [`docs/formats/FPK.md`](formats/fpk.md) | <span class="status pass">PASS</span> | 16,354/16,354 packages byte-identical, 732 Lua decode + compile |
| `formats/fox2.py` | Python | [`docs/formats/FOX2.md`](formats/fox2.md) | <span class="status pass">PASS</span> | 44,994/44,994 DataSets byte-identical |
| `formats/frt.py` | Python | [`docs/formats/FRT.md`](formats/frt.md) | <span class="status pass">PASS</span> | 307/307 route sets byte-identical |
| `formats/nav2.py` | Python (+numpy) | [`docs/NAVMESH.md`](formats/nav2.md) | <span class="status pass">PASS</span> | 840/840 navmeshes byte-identical |
| `formats/foxdata.py` | Python | [`docs/formats/FOXDATA.md`](formats/foxdata.md) | <span class="status pass">PASS</span> | 9,340/9,340 FoxData files (.htre .tre2 .geom .geoms .gskl) byte-identical |
| `formats/terrain.py` | Python (+numpy) | [`docs/formats/HTRE.md`](formats/htre.md) | <span class="status pass">PASS</span> | 4,164/4,164 .htre/.tre2 byte-identical, typed patch + arrays |
| `world/heightfield.py` | Python (+numpy, float32) | [`docs/formats/HTRE.md`](formats/htre.md) | <span class="status pass">PASS</span> | ground height by world position from `.htre` blocks / `.tre2` (triangle pair, block origin (b - 133) * 128) = live within 5 mm (`test_m7_ground.py`) |
| `runtime/` (gameobjects, scheduler, messages) | Python | [`docs/engine/Scheduler.md`](engine/scheduler.md), `Messages.md` | <span class="status pass">PASS</span> | live FoxTrace fixture: every updater-vector change and 43-message boot sequence reproduced (`test_m3_runtime.py`) |
| `script/` (host, vfs, foxmath.lua) | Python + Lua 5.1 (lupa) | [`docs/engine/ScriptHost.md`](engine/script-host.md) | <span class="status in-progress">IN PROGRESS</span> | boot runs the game's own init.lua + Tpp/start.lua with no error, 108 chunks in the live order up to the mission load (`test_m4_script_host.py`); API: 399 libraries from the binding map, 15 natives, 328 stubs touched |
| `world/` (identifiers, stage_blocks) | Python | [`docs/engine/World.md`](engine/world.md) | <span class="status pass">PASS</span> | DataIdentifier registry over the mounted DataSets: the title heli space's locator lookups match live for both saves and its OnAllocate finishes; FSTB large-block names/boxes vs live Block.* messages (`test_m6_world.py`); stage-block controller: Block.* messages = live for both saves; title UI (`runtime/title.py`: fade, splash screens, title menu, loading tips): title-menu messages = live and the title script's own CONTINUE reaches free roam (f30010, f30020) |
| `resources/` (loader, blocks, fstb) + pack mounts in `script/vfs.py` | Python | [`docs/engine/Resources.md`](engine/resources.md) | <span class="status in-progress">IN PROGRESS</span> | location/mission loading driven by the game's own Lua package lists, script blocks (8 slots), soldier common-motion block: 49/49 live chunks from live chunk 112 to the end of the boot (init -> title 40010 -> f30010 -> quest / reinforce / animal blocks; UI tables still excluded), block events and script-block loads match (`test_m5_mission_load.py`, `test_m5_script_blocks.py`) |

## Latest sessions

- 2026-11-06: **MOD-A G4 PASS** (MOD-A complete): live check `Tools\moda\livecheck.py`, spec ModToolkit.md "Live check [G4]"; edited route + rebaked 3 x 3 navmesh via SnakeBite (Luc); baker file-id bug found live and fixed (NAV2-HEADER); v2 runs `moda_g4d` / `e` clean; `test_moda_live.py` 9/9, gate MOD 4/8. Artifact: https://claude.ai/artifact/JHHhckNsLh75CXet5UJ1XK
- 2026-11-06: **MOD-A G3 PASS**: mod-Lua harness (`Tools\moda\luaharness.py`, 10 seeds, CLI `moda lua`), spec ModToolkit.md "Mod-Lua harness"; 2 live runs (Luc OK for the second: seed 07's `error()` at load ended the game); `test_moda_harness.py` 9/9, full suite 370/370, M10 14/14. Artifact: https://claude.ai/artifact/Dzg9Ae5bFKu6WLuedRwSMC
- 2026-11-06: **MOD-A G2 PASS**: navmesh baker (`Tools\moda\navbake.py`, `nav2mesh.py`, `nav2rules.py`), spec ModToolkit.md + NAVMESH.md "Build model" (0.1 m source grid); `test_moda_baker.py` 6/6, 1,297 / 1,348 queries within 0.1 m (938 / 948 M8 jobs); full suite PASS, M10 14/14. Artifact: https://claude.ai/artifact/SU8m5vR7yfv1QEnSnwGjAd
- 2026-11-06: **MOD-A G1 PASS**: ROADMAP MOD-A split into G1-G4 (gates.json MOD 8 items); spec [`docs\engine\ModToolkit.md`](engine/mod-toolkit.md); `Tools\moda\` validated writers (frt / fox2 / fpk, 30 rules) + `.frt` route editor + CLI; `test_moda_toolkit.py` 19/19 (307 vanilla `.frt` identical and clean, all 16,354 packages pass); full suite 355/355. Artifact: https://claude.ai/artifact/NqfjFmUpvbtRKCBp1afUew
- 2026-11-05: **M10 PASS (Luc)**: gate M10 14/14 (C3 N/A), statuses updated in ROADMAP, gates.json (M11 NEXT), README, site; full suite rerun PASS.

[Full session log](status/log.md)
