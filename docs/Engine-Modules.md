> [!NOTE]
> Generated `from[`Engine/README.md`](https://github.com/WannabeCoderLuc/mgsvtpp-foxre/blob/main/Engine/README.md)` on 2026-10-21. Edit the source doc; this page is overwritten on every sync. · [Home](index.md) · [Roadmap](Roadmap.md)

# Engine

Clean-room MGSV:TPP 1.0.15.4-compatible engine. Specs: `..\docs\formats\`, `..\docs\engine\`. Roadmap: `..\docs\ROADMAP.md`.
No game bytes in this folder; game data is read at runtime from the user's install / `GameBackup` / `EXTRACTED_DATA`.
Run all gates: MCP `engine_verify` (or `python -m pytest Engine\tests -q` from the repo root; ~6 min with a cold cache).

| Module | Lang | Spec | State | Gate (all files of the game) |
|---|---|---|---|---|
| `core/strcode.py` | Python | docstring | PASS | StrCode64 = exe 0x141A09AC0 (`re_emulate`, incl. > 64-byte strings) |
| `core/typedb.py` | Python | [docs/engine/Reflection.md](Engine-Reflection.md) | PASS | game registry dump == all DataSets (3,372/3,372 props) |
| `core/entities.py` | Python | [docs/engine/Entities.md](Engine-Entities.md) | PASS (static) | s10151: 8,669 entities typed, all refs resolved/categorised |
| `core/pathcode.py` | Python | [docs/formats/QAR.md](Format-QAR.md) | PASS | 111,394 QAR entry hashes matched by names |
| `formats/qar.py` | Python | [docs/formats/QAR.md](Format-QAR.md) | PASS | 134,241 entries MD5-verified, headers/tables re-encode exactly |
| `formats/fpk.py` | Python | [docs/formats/FPK.md](Format-FPK.md) | PASS | 16,354/16,354 packages byte-identical, 732 Lua decode + compile |
| `formats/fox2.py` | Python | [docs/formats/FOX2.md](Format-FOX2.md) | PASS | 44,994/44,994 DataSets byte-identical |
| `formats/frt.py` | Python | [docs/formats/FRT.md](Format-FRT.md) | PASS | 307/307 route sets byte-identical |
| `formats/nav2.py` | Python (+numpy) | [docs/NAVMESH.md](Format-NAV2.md) | PASS | 840/840 navmeshes byte-identical |

`Tools\foxhash.py` and `Tools\nav2lib.py` are shims to `core/strcode.py` and `formats/nav2.py`.
Tests: `tests\` (pytest; `verifiers.lock.json` = sha256 of each verifier, enforced by `engine_verify`). Census tools that produce the spec statistics: `Tools\{fox2,fpk,qar}_census.py`, `Tools\qar_harvest_paths.py`.
