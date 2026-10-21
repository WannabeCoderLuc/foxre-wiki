# Engine modules

Clean-room MGSV:TPP 1.0.15.4-compatible engine. Specs: `..\docs\formats\`, `..\docs\engine\`. Roadmap: [`..\docs\ROADMAP.md`](../status/roadmap.md).
No game bytes in this folder; game data is read at runtime from the user's install / `GameBackup` / `EXTRACTED_DATA`.
Run all gates: MCP `engine_verify` (or `python -m pytest Engine\tests -q` from the repo root; ~6 min with a cold cache).

| Module | Lang | Spec | State | Gate (all files of the game) |
|---|---|---|---|---|
| `core/strcode.py` | Python | docstring | <span class="status pass">PASS</span> | StrCode64 = exe 0x141A09AC0 (`re_emulate`, incl. > 64-byte strings) |
| `core/typedb.py` | Python | [`docs/engine/Reflection.md`](reflection.md) | <span class="status pass">PASS</span> | game registry dump == all DataSets (3,372/3,372 props) |
| `core/entities.py` | Python | [`docs/engine/Entities.md`](entities.md) | <span class="status pass">PASS</span> | s10151: 8,669 entities typed, all refs resolved/categorised; live: 17/17 f30010 identifier targets match the game |
| `core/pathcode.py` | Python | [`docs/formats/QAR.md`](../formats/qar.md) | <span class="status pass">PASS</span> | 111,394 QAR entry hashes matched by names |
| `formats/qar.py` | Python | [`docs/formats/QAR.md`](../formats/qar.md) | <span class="status pass">PASS</span> | 134,241 entries MD5-verified, headers/tables re-encode exactly |
| `formats/fpk.py` | Python | [`docs/formats/FPK.md`](../formats/fpk.md) | <span class="status pass">PASS</span> | 16,354/16,354 packages byte-identical, 732 Lua decode + compile |
| `formats/fox2.py` | Python | [`docs/formats/FOX2.md`](../formats/fox2.md) | <span class="status pass">PASS</span> | 44,994/44,994 DataSets byte-identical |
| `formats/frt.py` | Python | [`docs/formats/FRT.md`](../formats/frt.md) | <span class="status pass">PASS</span> | 307/307 route sets byte-identical |
| `formats/nav2.py` | Python (+numpy) | [`docs/NAVMESH.md`](../formats/nav2.md) | <span class="status pass">PASS</span> | 840/840 navmeshes byte-identical |

`Tools\foxhash.py` and `Tools\nav2lib.py` are shims to `core/strcode.py` and `formats/nav2.py`.
Tests: `tests\` (pytest; `verifiers.lock.json` = sha256 of each verifier, enforced by `engine_verify`). Census tools that produce the spec statistics: `Tools\{fox2,fpk,qar}_census.py`, `Tools\qar_harvest_paths.py`.

---
<small>Source: `Engine/README.md` in the project repository &middot; generated 2026-10-22.</small>
