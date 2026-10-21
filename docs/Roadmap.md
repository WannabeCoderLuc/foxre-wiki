> [!NOTE]
> Generated `from[`docs/ROADMAP.md`](https://github.com/WannabeCoderLuc/mgsvtpp-foxre/blob/main/docs/ROADMAP.md)` on 2026-10-21. Edit the source doc; this page is overwritten on every sync. · [Home](index.md) · [Roadmap](Roadmap.md)

# Roadmap: clean-room MGSV:TPP-compatible engine

Goal: an engine in `Engine\` that loads the player's own MGSV:TPP 1.0.15.4 data and reproduces its behaviour, written from specs (`docs\formats\`, `docs\engine\`), never from copied game code or assets. Every milestone ends on a **machine-decidable gate** (lesson from awesome-rea, [docs/TOOLING.md](Tooling.md)); a milestone is done only when `engine_verify` is green for its gate tests.

Status keys: PASS = gate passed · IN PROGRESS · PLANNED. Update this file when a gate passes.

## M0 Foundations [PASS] (2026-10-21)
- Workspace, docs, git repo, MCP `mgsv-unified` 1.4.0 (30 tools), knowledge DB, skills.
- Oracles: `re_emulate` (exe function in unicorn), `engine_verify` (pytest + verifier lock), `lua51_run` (Lua 5.1 sandbox).
- StrCode32/64 verified vs the exe (`Tools\foxhash.py`, incl. > 64-byte CityHash 1.1 body). `.nav2` codec byte-identical on 853 files.
- **Gate passed:** `engine_verify` 9/9.

## M1 Data layer [PASS] (gates passed 2026-10-21) — read every file container and the core data formats
| Item | Prior work | Gate |
|---|---|---|
| PASS: QAR `.dat` archives + PathCode64 | `Engine/formats/qar.py`, `Engine/core/pathcode.py`, [docs/formats/QAR.md](Format-QAR.md) | **passed 2026-10-21: 134,241/134,241 entries MD5-verified in 13 archives; headers/tables re-encode exactly; 83.0 % named** |
| PASS: `.fpk`/`.fpkd` packages | `Engine/formats/fpk.py`, [docs/formats/FPK.md](Format-FPK.md) | **passed 2026-10-21: 16,354/16,354 unique packages byte-identical; 732/732 Lua entries decode + compile** |
| PASS: `.fox2` DataSets | `Engine/formats/fox2.py`, [docs/formats/FOX2.md](Format-FOX2.md) | **passed 2026-10-21: 44,994/44,994 unique DataSets byte-identical**; name resolution % still to report |
| PASS: `.frt` routes, `.nav2` | `Engine/formats/frt.py` + [docs/formats/FRT.md](Format-FRT.md), `Engine/formats/nav2.py` + [docs/NAVMESH.md](Format-NAV2.md) | **passed 2026-10-21: 307/307 route files and 840/840 navmeshes byte-identical**; 69/104 route event types named |
| PASS: `.lua` in packs | `fpk.decode_entry` | **732/732 decode + compile** (in the FPK gate) |
| `.sdf`/`.sbp` sound packages (container only) | — | listed + byte-extract — moved to M6/M8 (sound) |
Remaining M1 polish: FOX2 name-resolution %, texture name gap (22.8k unnamed `.ftexs`), exe-side parser VAs (all [?]).
Output: `Engine\formats\` (ported from ATOMIZER/Tools into one package), `docs\formats\{QAR,FPK,FOX2,FRT,NAV2}.md`. Skill: `fox-format`.

## M2 Entity & reflection core [IN PROGRESS] — fox2 → live typed entity graph
- PASS: Reflection spec + type DB (2026-10-21): the game's own registry dump (`Fox.ExportSerializeInfo()`, 1,153 classes / 6,062 properties) → `Engine/core/typedb.py`, [docs/engine/Reflection.md](Engine-Reflection.md); matches all 44,994 DataSets (3,372/3,372 properties, all versions; 17 Fx node classes only in data).
- PASS: Entity graph (static, 2026-10-21): `Engine/core/entities.py`, [docs/engine/Entities.md](Engine-Entities.md) — s10151 + link closure: 8,669 entities 100 % typed, 7,728/7,728 EntityPtr, all handles/links resolved or in named categories.
- PLANNED: Runtime instantiation spec (factory, field offsets, DataSet name map) + live fixture of one loaded DataSet → closes M2.
- **Gate:** load all DataSets of one mission (e.g. s10151) into typed entities; 100 % classes and properties typed; references resolve; live fixture (entity counts/values after load) matches.
Skills: `fox-system`, `fox-ground-truth`, `fox-engine-module`.

## M3 Runtime core [PLANNED] — scheduler, messages, GameObjects
- Quark system table, GameObjectManager/TypeManager, 3-phase tick, MessageBus, SendCommand dispatch ([docs/ENGINE.md](Engine-Core-Architecture.md) milestone 3).
- **Gate:** live fixtures for one frame's tick order and the message sequence of a mission start reproduced by the engine's scheduler model.

## M4 Script host [PLANNED] — Lua 5.1 + Fox/Tpp API
- Lua 5.1 host (lupa prototype → embedded), the Fox/Tpp/GameObject API surface (264 native bindings, 2,433 used API functions in `mgsv_query_knowledge(lua_api)`), StrCode in Lua.
- **Gate:** `TppDefine`, `TppMain` and one mission script load and run their init with no unstubbed API calls (coverage % reported by `lua51_run`), API call log matches a live capture.

## M5 World [PLANNED] — terrain, collision, navigation, routes
- `.htre`/`.tre2` terrain, `.geom` collision, nav2 A* over portal graph, route following.
- **Gate:** path queries equal live `RequestMove` results (fixtures); heightmap samples equal live ground heights.

## M6 Assets & rendering [PLANNED]
- `.ftex/.ftexs`, `.fmdl`, `.fv2`/fova, `.parts`, materials/shaders; viewer (D3D11 or Vulkan, ImGui via vcpkg).
- **Gate:** all textures/models decode; RenderDoc captures of reference frames vs engine frames (per-pass image diff within tolerance).

## M7 Animation [PLANNED]
- `.mtar`/`.gani`, `.mog` motion graph, `.frig`/`.frdv` rigs, motion events.
- **Gate:** sampled poses equal live captured bone transforms for reference clips.
- Note (2026-10-21, community): youarebritish (FoxKit / FoxEngineTemplates author) says **motion graphs (`.mog`) are among the least understood Fox formats** — a realistic, valuable target where this project can contribute new knowledge. Milestone scope unchanged.

## M8 Gameplay systems [PLANNED]
- GameObject families (Player2, Soldier2, Sahelan2 — [docs/SAHELAN.md](https://github.com/WannabeCoderLuc/mgsvtpp-foxre/blob/main/docs/SAHELAN.md) is the deepest spec), AI framework (node tables, blackboard), damage, sound (Wwise containers).
- **Gate:** per system, behaviour fixtures (state sequences) reproduced.

## M9 Playable slice [PLANNED]
- One free-roam area streamed in, player controllable (KB+M), one AI type alive.
- **Gate:** scripted 60 s input replay produces the same state trace as the live game within tolerance.

## Parked track: Option B mod (Sahelanthropus pilot) — on hold until M3/M4 (Luc, 2026-10-21)
Feature-complete pending Luc's playtests (`STATUS.md`). Its RE ([docs/SAHELAN.md](https://github.com/WannabeCoderLuc/mgsvtpp-foxre/blob/main/docs/SAHELAN.md), `docs\PROBES.md`) feeds M8.
