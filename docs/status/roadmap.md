# Roadmap

Goal: an engine in `Engine\` that loads the player's own MGSV:TPP 1.0.15.4 data and reproduces its behaviour, written from specs (`docs\formats\`, `docs\engine\`), never from copied game code or assets. Every milestone ends on a **machine-decidable gate** (lesson from awesome-rea, [`docs\TOOLING.md`](../tools/tooling.md)); a milestone is done only when `engine_verify` is green for its gate tests.

Status keys: PASS = gate passed · IN PROGRESS · PLANNED. Update this file when a gate passes.

## M0 Foundations [PASS] (2026-10-21) — workspace, MCP oracles, hash functions
- Workspace, docs, git repo, MCP `mgsv-unified` 1.4.0 (30 tools), knowledge DB, skills.
- Oracles: `re_emulate` (exe function in unicorn), `engine_verify` (pytest + verifier lock), `lua51_run` (Lua 5.1 sandbox).
- StrCode32/64 verified vs the exe (`Tools\foxhash.py`, incl. > 64-byte CityHash 1.1 body). `.nav2` codec byte-identical on 853 files.
- **Gate passed:** `engine_verify` 9/9.

## M1 Data layer [PASS] (gates passed 2026-10-21) — read every file container and the core data formats
| Item | Prior work | Gate |
|---|---|---|
| PASS: QAR `.dat` archives + PathCode64 | `Engine/formats/qar.py`, `Engine/core/pathcode.py`, [`docs/formats/QAR.md`](../formats/qar.md) | **passed 2026-10-21: 134,241/134,241 entries MD5-verified in 13 archives; headers/tables re-encode exactly; 83.0 % named** |
| PASS: `.fpk`/`.fpkd` packages | `Engine/formats/fpk.py`, [`docs/formats/FPK.md`](../formats/fpk.md) | **passed 2026-10-21: 16,354/16,354 unique packages byte-identical; 732/732 Lua entries decode + compile** |
| PASS: `.fox2` DataSets | `Engine/formats/fox2.py`, [`docs/formats/FOX2.md`](../formats/fox2.md) | **passed 2026-10-21: 44,994/44,994 unique DataSets byte-identical**; name resolution % still to report |
| PASS: `.frt` routes, `.nav2` | `Engine/formats/frt.py` + [`docs/formats/FRT.md`](../formats/frt.md), `Engine/formats/nav2.py` + [`docs/NAVMESH.md`](../formats/nav2.md) | **passed 2026-10-21: 307/307 route files and 840/840 navmeshes byte-identical**; 69/104 route event types named |
| PASS: `.lua` in packs | `fpk.decode_entry` | **732/732 decode + compile** (in the FPK gate) |
| `.sdf`/`.sbp` sound packages (container only) | — | listed + byte-extract — moved to M6/M8 (sound) |

Remaining M1 polish: FOX2 name-resolution %, texture name gap (22.8k unnamed `.ftexs`), exe-side parser VAs (all [?]).
Output: `Engine\formats\` (ported from ATOMIZER/Tools into one package), `docs\formats\{QAR,FPK,FOX2,FRT,NAV2}.md`. Skill: `fox-format`.

## M2 Entity & reflection core [PASS] (gates passed 2026-10-21) — fox2 → live typed entity graph
- PASS: Reflection spec + type DB (2026-10-21): the game's own registry dump (`Fox.ExportSerializeInfo()`, 1,153 classes / 6,062 properties) → `Engine/core/typedb.py`, [`docs/engine/Reflection.md`](../engine/reflection.md); matches all 44,994 DataSets (3,372/3,372 properties, all versions; 17 Fx node classes only in data).
- PASS: Entity graph (static, 2026-10-21): `Engine/core/entities.py`, [`docs/engine/Entities.md`](../engine/entities.md) — s10151 + link closure: 8,669 entities 100 % typed, 7,728/7,728 EntityPtr, all handles/links resolved or in named categories.
- PASS: Runtime instantiation decoded (format select 0x1400ED040, binary reader state machine 0x1400EDE50, arena allocation, writer 0x1400EF290) → [`docs/engine/Entities.md`](../engine/entities.md); live gate: 17/17 f30010 DataIdentifier targets (name, class, world translation) match the running game (`test_live_f30010_identifiers.py`).
- **Gate:** load all DataSets of one mission (e.g. s10151) into typed entities; 100 % classes and properties typed; references resolve; live fixture (entity counts/values after load) matches.
Skills: `fox-system`, `fox-ground-truth`, `fox-engine-module`.

## M3 Runtime core [PASS] (gate passed 2026-10-22) — scheduler, messages, GameObjects
- Quark system table, GameObjectManager/TypeManager, 3-phase tick, MessageBus, SendCommand dispatch ([`docs\ENGINE.md`](../engine/core-architecture.md) milestone 3).
- PASS: Scheduler re-verified → [`docs/engine/Scheduler.md`](../engine/scheduler.md) (GOM tick: creation queue + 3 per-type phases; per-frame job 0x140BF5350 = GOM tick + priority-sorted updaters in 4 groups).
- PASS: Messages re-verified → [`docs/engine/Messages.md`](../engine/messages.md) (MessageBus Quark+0x60 vt+0x40, 4-arg payload with 3-bit type tags; SendCommand → TypeManager vt+0x80; SendMessage per-type Lua-ref FIFO).
- PASS: live capture FoxTrace 1 (`Tools/FoxTrace/`, log-only MinHook on job 0x140BF5350, RaiseMessage 0x140BF3A30, listener 0x140BF9A20), 2 boots identical → `Engine/tests/fixtures/m3_frame_trace.json` (3 updater vectors 18/19/24, 4 type groups, 43 messages).
- PASS: `Engine/runtime/` (gameobjects, scheduler, messages); `test_m3_runtime.py` 9/9, full suite 28/28.
- Open (not gate-blocking): updater identities, who walks the 4 type groups, when the GameObject listener fires, updater removal path, >32-updater sort.
- **Gate passed:** live fixtures for the tick order (every captured updater-vector change, ties included) and the boot → free-roam message sequence reproduced by the engine's scheduler/bus model.

## M4 Script host [IN PROGRESS] — Lua 5.1 + Fox/Tpp API
- Spec [`docs\engine\ScriptHost.md`](../engine/script-host.md) (2026-10-22): Lua runtime = stock 5.1 except TString chars behind a pointer [V]; live boot capture (FoxTrace 2): 170-chunk boot order, 147 library registrations, identical over 2 runs → `Engine	ests
ixtures\m4_lua_boot.json`.
- Lua 5.1 host (lupa prototype → embedded), the Fox/Tpp/GameObject API surface (264 native bindings, 2,433 used API functions in `mgsv_query_knowledge(lua_api)`), StrCode in Lua.
- **Gate:** `TppDefine`, `TppMain` and one mission script load and run their init with no unstubbed API calls (coverage % reported by `lua51_run`), API call log matches a live capture.

## M5 World [PLANNED] — terrain, collision, navigation, routes
- `.htre`/`.tre2` terrain, `.geom` collision, nav2 A* over portal graph, route following.
- **Gate:** path queries equal live `RequestMove` results (fixtures); heightmap samples equal live ground heights.

## M6 Assets & rendering [PLANNED] — textures, models, materials, renderer
- `.ftex/.ftexs`, `.fmdl`, `.fv2`/fova, `.parts`, materials/shaders; viewer (D3D11 or Vulkan, ImGui via vcpkg).
- **Gate:** all textures/models decode; RenderDoc captures of reference frames vs engine frames (per-pass image diff within tolerance).

## M7 Animation [PLANNED] — clips, motion graphs, rigs
- `.mtar`/`.gani`, `.mog` motion graph, `.frig`/`.frdv` rigs, motion events.
- **Gate:** sampled poses equal live captured bone transforms for reference clips.
- Note (2026-10-21, community): youarebritish (FoxKit / FoxEngineTemplates author) says **motion graphs (`.mog`) are among the least understood Fox formats** — a realistic, valuable target where this project can contribute new knowledge. Milestone scope unchanged.

## M8 Gameplay systems [PLANNED] — GameObject families, AI, damage, sound
- GameObject families (Player2, Soldier2, Sahelan2 — `docs\SAHELAN.md` is the deepest spec), AI framework (node tables, blackboard), damage, sound (Wwise containers).
- **Gate:** per system, behaviour fixtures (state sequences) reproduced.

## M9 Playable slice [PLANNED] — one free-roam area, player + one AI type
- One free-roam area streamed in, player controllable (KB+M), one AI type alive.
- **Gate:** scripted 60 s input replay produces the same state trace as the live game within tolerance.

## Parked track: Option B mod (Sahelanthropus pilot) — on hold until M3/M4 (Luc, 2026-10-21)
Feature-complete pending Luc's playtests (`STATUS.md`). Its RE (`docs\SAHELAN.md`, `docs\PROBES.md`) feeds M8.

---
<small>Source: `docs/ROADMAP.md` in the project repository &middot; generated 2026-10-22.</small>
