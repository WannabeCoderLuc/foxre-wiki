<div class="wiki-hero">

# FoxRe Wiki

### Fox Engine Reverse Engineering & Architecture Reference

<div class="hero-badges">
<span class="hero-badge">Target: PC 1.0.15.4 EN</span>
<span class="hero-badge">Runtime Hooks Only</span>
<span class="hero-badge">Clean-Room Verified</span>
<span class="hero-badge">Machine-Checked Gates</span>
</div>


**Reverse engineering *Metal Gear Solid V: The Phantom Pain* and rebuilding its Fox Engine — clean-room and test-gated.**

`PC 1.0.15.4 EN` · `runtime hooks only` · `no game files in this repo` · `every claim backed by a machine-checked gate`

<div class="progress-bar-container"><div class="progress-bar-fill" style="width: 25%"></div></div><br>
**2 / 10 milestones done** · now: **M2 Entity & reflection core**

</div>

---

## Start here
| | |
|---|---|
| **[Roadmap](Roadmap.md)** | Milestones M0–M9 and the PASS/FAIL gate each one must meet |
| **[Engine modules](Engine-Modules.md)** | What exists in `Engine/` today and how it is verified |
| **File formats** | [QAR](Format-QAR.md) · [FPK](Format-FPK.md) · [FOX2](Format-FOX2.md) · [FRT](Format-FRT.md) · [NAV2](Format-NAV2.md) |
| **Engine internals** | [Reflection / type DB](Engine-Reflection.md) · [Entities](Engine-Entities.md) · [Core architecture](Engine-Core-Architecture.md) |
| **Game systems** | [Sahelanthropus](https://github.com/WannabeCoderLuc/mgsvtpp-foxre/blob/main/docs/SAHELAN.md) · [Battlefield AI](https://github.com/WannabeCoderLuc/mgsvtpp-foxre/blob/main/docs/BATTLEFIELD.md) |
| **Tooling** | [MCP server](MCP-Server.md) · [Tooling](Tooling.md) · [Background](Background.md) |

## Milestones
| | Milestone | Status |
|---|---|:-:|
| **M0** | Foundations | <span class="status-badge status-pass">PASS</span> |
| **M1** | Data layer — read every file container and the core data formats | <span class="status-badge status-pass">PASS</span> |
| **M2** | Entity & reflection core — fox2 → live typed entity graph | <span class="status-badge status-wip">IN PROGRESS</span> |
| **M3** | Runtime core — scheduler, messages, GameObjects | <span class="status-badge status-planned">PLANNED</span> |
| **M4** | Script host — Lua 5.1 + Fox/Tpp API | <span class="status-badge status-planned">PLANNED</span> |
| **M5** | World — terrain, collision, navigation, routes | <span class="status-badge status-planned">PLANNED</span> |
| **M6** | Assets & rendering | <span class="status-badge status-planned">PLANNED</span> |
| **M7** | Animation | <span class="status-badge status-planned">PLANNED</span> |
| **M8** | Gameplay systems | <span class="status-badge status-planned">PLANNED</span> |
| **M9** | Playable slice | <span class="status-badge status-planned">PLANNED</span> |

## <span class="status-badge status-pass">PASS</span> Verified so far
| Module | Lang | Spec | State | Gate (on all game files) |
|---|---|---|---|---|
| `core/strcode.py` | Python | docstring | <span class="status-badge status-pass">PASS</span> | StrCode64 = exe 0x141A09AC0 (`re_emulate`, incl. > 64-byte strings) |
| `core/typedb.py` | Python | [docs/engine/Reflection.md](Engine-Reflection.md) | <span class="status-badge status-pass">PASS</span> | game registry dump == all DataSets (3,372/3,372 props) |
| `core/entities.py` | Python | [docs/engine/Entities.md](Engine-Entities.md) | <span class="status-badge status-pass">PASS</span> static | s10151: 8,669 entities typed, all refs resolved/categorised |
| `core/pathcode.py` | Python | [docs/formats/QAR.md](Format-QAR.md) | <span class="status-badge status-pass">PASS</span> | 111,394 QAR entry hashes matched by names |
| `formats/qar.py` | Python | [docs/formats/QAR.md](Format-QAR.md) | <span class="status-badge status-pass">PASS</span> | 134,241 entries MD5-verified, headers/tables re-encode exactly |
| `formats/fpk.py` | Python | [docs/formats/FPK.md](Format-FPK.md) | <span class="status-badge status-pass">PASS</span> | 16,354/16,354 packages byte-identical, 732 Lua decode + compile |
| `formats/fox2.py` | Python | [docs/formats/FOX2.md](Format-FOX2.md) | <span class="status-badge status-pass">PASS</span> | 44,994/44,994 DataSets byte-identical |
| `formats/frt.py` | Python | [docs/formats/FRT.md](Format-FRT.md) | <span class="status-badge status-pass">PASS</span> | 307/307 route sets byte-identical |
| `formats/nav2.py` | Python (+numpy) | [docs/NAVMESH.md](Format-NAV2.md) | <span class="status-badge status-pass">PASS</span> | 840/840 navmeshes byte-identical |

## Latest
- 2026-10-21: M2 entity graph (static): s10151 + link closure → 8,669 typed entities, all refs resolved or categorised (`docs\engine\Entities.md`).
- 2026-10-21: M2 reflection: game type DB dumped live (1,153 classes, 6,062 props) → `Engine\core\typedb.py`, `docs\engine\Reflection.md`; matches all DataSets. Game run restored to baseline.
- 2026-10-21: **M1 done**: FPK 16,354/16,354, QAR 134,241 entries MD5-ok, FRT 307/307, NAV2 840/840; 68 route event names recovered.
- 2026-10-21: M1 FOX2 gate passed (44,994/44,994 byte-identical); `docs/formats/FOX2.md`; ENGINE.md §1.2 marked wrong.
- 2026-10-21: roadmap `docs\ROADMAP.md`; skills list MCP usage; docs synced.

[Full session log →](Session-Log.md)

---
<sub>Generated 2026-10-21 from the repo docs by `Tools/build_wiki.py` · synced on every docs push by the *Sync wiki* GitHub Action.</sub>
