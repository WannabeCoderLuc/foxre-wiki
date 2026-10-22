---
hide:
  - toc
---

<div class="hero" markdown>

# FoxRe

**Reverse engineering *Metal Gear Solid V: The Phantom Pain* and rebuilding its Fox Engine — clean-room, test-gated.**

PC 1.0.15.4 &middot; runtime analysis only &middot; no game files published &middot; every claim backed by a pass/fail test

**4 of 10 milestones passed** &middot; current: **M4 Script host**

</div>

<div class="grid cards" markdown>

-   **[Guide](guide/index.md)**

    Plain-language explanations of how the game's data and engine work. Start here.

-   **[Engine](engine/index.md)**

    Specifications of engine subsystems and the state of the new engine.

-   **[File formats](formats/index.md)**

    Byte-level format specs, each verified on every game file.

-   **[Project status](status/index.md)**

    Roadmap with milestone gates, and the full session log.

</div>

## Milestones

| | Milestone | Scope | Status |
|---|---|---|:-:|
| M0 | Foundations | workspace, MCP oracles, hash functions | <span class="status pass">PASS</span> |
| M1 | Data layer | read every file container and the core data formats | <span class="status pass">PASS</span> |
| M2 | Entity & reflection core | fox2 → live typed entity graph | <span class="status pass">PASS</span> |
| M3 | Runtime core | scheduler, messages, GameObjects | <span class="status pass">PASS</span> |
| M4 | Script host | Lua 5.1 + Fox/Tpp API | <span class="status in-progress">IN PROGRESS</span> |
| M5 | World | terrain, collision, navigation, routes | <span class="status planned">PLANNED</span> |
| M6 | Assets & rendering | textures, models, materials, renderer | <span class="status planned">PLANNED</span> |
| M7 | Animation | clips, motion graphs, rigs | <span class="status planned">PLANNED</span> |
| M8 | Gameplay systems | GameObject families, AI, damage, sound | <span class="status planned">PLANNED</span> |
| M9 | Playable slice | one free-roam area, player + one AI type | <span class="status planned">PLANNED</span> |

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

## Latest sessions

- 2026-10-22: **M4 binding map** (4 FoxTrace captures, hook-race fix): `m4_lua_bindings.json` 399 libs / 5,532 bindings, static oracle test; chunk loading C side, per-frame C → Lua callers. mod-baseline re-snapshot without V Framework.
- 2026-10-22: **MCP 1.5.0** (11-item tool upkeep, selftest 39/39, FoxTrace 2) + **M4 started**: Lua layout [V], live boot capture (170 chunks, 147 libs, 2 identical runs) → `m4_lua_boot.json`, [`docs\engine\ScriptHost.md`](engine/script-host.md). Nexus: IH/IHHook current.
- 2026-10-22: **M3 PASS**: FoxTrace live capture (2 identical boots) → `m3_frame_trace.json`; `Engine\runtime\` reproduces updater order + message sequence; suite 28/28. Site tables fixed.
- 2026-10-21: M3 specs: scheduler + messages re-verified from the exe ([`docs\engine\Scheduler.md`](engine/scheduler.md), `Messages.md`); 3 FoxRe claims corrected.
- 2026-10-21: **M2 PASS**: DataSet reader/writer decoded (magic checked, ASCII version, instanceSize, classVersion check); live gate 17/17 identifier targets match the game. Pages site + text statuses set up.

[Full session log](status/log.md)
