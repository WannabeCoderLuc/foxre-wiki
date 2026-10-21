---
hide:
  - toc
---

<div class="hero" markdown>

# FoxRe

**Reverse engineering *Metal Gear Solid V: The Phantom Pain* and rebuilding its Fox Engine — clean-room, test-gated.**

PC 1.0.15.4 &middot; runtime analysis only &middot; no game files published &middot; every claim backed by a pass/fail test

**3 of 10 milestones passed** &middot; current: **M3 Runtime core**

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
| M0 | Foundations |  | <span class="status pass">PASS</span> |
| M1 | Data layer | read every file container and the core data formats | <span class="status pass">PASS</span> |
| M2 | Entity & reflection core | fox2 → live typed entity graph | <span class="status pass">PASS</span> |
| M3 | Runtime core | scheduler, messages, GameObjects | <span class="status in-progress">IN PROGRESS</span> |
| M4 | Script host | Lua 5.1 + Fox/Tpp API | <span class="status planned">PLANNED</span> |
| M5 | World | terrain, collision, navigation, routes | <span class="status planned">PLANNED</span> |
| M6 | Assets & rendering |  | <span class="status planned">PLANNED</span> |
| M7 | Animation |  | <span class="status planned">PLANNED</span> |
| M8 | Gameplay systems |  | <span class="status planned">PLANNED</span> |
| M9 | Playable slice |  | <span class="status planned">PLANNED</span> |

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

## Latest sessions

- 2026-10-21: M3 specs: scheduler + messages re-verified from the exe ([`docs\engine\Scheduler.md`](engine/scheduler.md), `Messages.md`); 3 FoxRe claims corrected.
- 2026-10-21: **M2 PASS**: DataSet reader/writer decoded (magic checked, ASCII version, instanceSize, classVersion check); live gate 17/17 identifier targets match the game. Pages site + text statuses set up.
- 2026-10-21: M2 entity graph (static): s10151 + link closure → 8,669 typed entities, all refs resolved or categorised ([`docs\engine\Entities.md`](engine/entities.md)).
- 2026-10-21: M2 reflection: game type DB dumped live (1,153 classes, 6,062 props) → `Engine\core\typedb.py`, [`docs\engine\Reflection.md`](engine/reflection.md); matches all DataSets. Game run restored to baseline.
- 2026-10-21: **M1 done**: FPK 16,354/16,354, QAR 134,241 entries MD5-ok, FRT 307/307, NAV2 840/840; 68 route event names recovered.

[Full session log](status/log.md)
