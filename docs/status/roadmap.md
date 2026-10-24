# Roadmap

Goal: an engine in `Engine\` that loads the player's own MGSV:TPP 1.0.15.4 data and reproduces its behaviour, written from specs (`docs\formats\`, `docs\engine\`), never from copied game code or assets. Every milestone ends on a **machine-decidable gate** (lesson from awesome-rea, [`docs\TOOLING.md`](../tools/tooling.md)); a milestone is done only when `engine_verify` is green for its gate tests.

Status keys: PASS = gate passed · IN PROGRESS · PLANNED. Update this file when a gate passes.

**Principles:** headless first (renderer last); every gate is checked against live traces; formats are decoded when a milestone first needs them. Order re-agreed with Luc 2026-10-22 (new M5 Resources & mission load; old M5 World → M6, M6 Assets & rendering → M10, M8 split into M8/M9, M9 → M11).

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
| `.sdf`/`.sbp` sound packages (container only) | — | listed + byte-extract — moved to M9 (sound) |

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
- Spec [`docs\engine\ScriptHost.md`](../engine/script-host.md) (2026-10-22): Lua runtime = stock 5.1 except TString chars behind a pointer [V]; live boot capture (FoxTrace 2): 170-chunk boot order, 147 library registrations, identical over 2 runs → `Engine\tests\fixtures\m4_lua_boot.json`.
- [x] Native binding map (2026-10-22): 4 registration paths (luaI_openlib, Fox table builder, Fox class tables, direct setfield) [V]; 399 libraries / 5,532 bindings / 2,286 enum values, 2 identical runs + static oracle → `Engine\tests\fixtures\m4_lua_bindings.json`, `test_m4_bindings.py`.
- [x] C side of chunk loading (Fox dofile, 0x1B/0x1C decode, boot coroutine, Script.LoadLibrary*) and per-frame C → Lua callers (OnUpdate, ScriptUpdater, OnSynchronizeSVars) [V].
- [x] Host boot (2026-10-22): `Engine\script\` runs init.lua + Tpp/start.lua (coroutine per frame) with no error; 108 chunks in the exact live order up to the mission load; static plain-value constants (`m4_lua_consts.json`).
- Lua 5.1 host (lupa prototype → embedded), the Fox/Tpp/GameObject API surface (264 native bindings, 2,433 used API functions in `mgsv_query_knowledge(lua_api)`), StrCode in Lua.
- [x] Record/replay started (2026-10-23): FoxTrace 3 `luaret` (thunk + direct `lua_CFunction` return recorder), 2 captures x 2 identical runs -> `m4_lua_returns.json` (536 names, 534 stable); host replay answers 89.1 % of the API the M5 scenario touches (6.4 % without) and the f30010 `OnAllocate`/`OnInitialize` finish (`test_m4_replay.py`). Open: table-valued natives (svars declarations), 48 remaining stubs, API call-log comparison.
- **Gate (re-agreed 2026-10-22):** init + f30010 mission scripts run against **recorded** native return values (record/replay fixture from a live capture); chunk order and API call log match the live capture. (Dropped: "no unstubbed API calls"; natives are answered from the replay fixture.)

## M5 Resources & mission load [PASS] — packs, blocks, async resources, mission start
- Pack/block system, async resource requests, the mission load flow (`start2nd.lua` / `TppMission` / block groups), pack-scoped VFS (mission scripts become visible only once their pack is loaded). Spec [`docs\engine\Resources.md`](../engine/resources.md).
- [x] Mission load decoded (2026-10-23, [`docs\engine\Resources.md`](../engine/resources.md)): `Mission.LoadLocation/LoadMission` latch requests; location loader + mission block controller (vtable 0x1422A9710, from `TppSimpleMissionBlockControllerData`) ask the Lua package-path functions; `.lua` entries of loaded packages are script resources (reverse entry order); `OnAllocate`/`OnInitialize` coroutines; `mvars` reset by the mission object [V].
- [x] `Engine\resources\` (loader, FSTB common-package header) + pack-scoped `Engine\script\vfs.py`: host loads **46 chunks in the exact live order** from live chunk 112 (init → title 40010 → f30010, minus 9 UI tables), block events match (`test_m5_mission_load.py`).
- [x] Script blocks (2026-10-23): 8-slot system decoded (`ScriptBlock.*`, slot update 0x140184340, OnAllocate/OnInitialize/OnUpdate/OnTerminate) → `Engine\resources\blocks.py`; svars change log → `OnChangeSVars`, mission `OnUpdate`, save boundary `LoadVarsFromSlot` (live save image), 2nd luaret capture (663 natives) + IH Lua trace. Host loads **49/49 chunks from live 112 to the end of the boot** (UI tables excluded), script blocks quest / reinforce / animal in vanilla order, slots and `ScriptBlock.Load` calls as live (`test_m5_mission_load.py`, `test_m5_script_blocks.py`). Live tail order differs only by IH's patched `f30010.fpkd` [V].
- [x] UI parameter tables (2026-10-24): the `mbdvc_*` tables are `mb_dvc_top.fpk` scripts, reloaded by the iDroid on every `TppUiCommand.ChangeLanguage()` (3 per boot: TppUiBootInit, init_sequence SetSavedLanguage, CreateOrLoadSaveData), `emblem_list.lua` from the emblem setup 0x1405CF950 [V static + live capture `trace_m5_lang`] → `Engine\resources\ui.py` (`IDroid`). Host boot: 112/112 live chunks (boot UI load asserted as an async group: live order varies between runs); M5 scenario: **58/58 live chunks from 112** (the title flow's language changes and loads at the native boundary).
- **Gate passed (2026-10-24):** chunk + block event order from live chunk 112 to the end of the boot (`m4_lua_boot.json` chunks 112–169) reproduced by the host.

## Mod checkpoint (after M5) — short Option B sprint
- Luc's playtests (V_Sahelan / Unbound t2b), gatling soldier damage, cockpit view framing, using the M0–M5 findings. Then on to M6.

## M6 World [PLANNED] — terrain, collision, navigation, routes
- `.htre`/`.tre2` terrain, `.geom` collision, nav2 A* over portal graph, route following.
- **Gate:** path queries equal live `RequestMove` results (fixtures); heightmap samples equal live ground heights.

## M7 Animation [PLANNED] — clips, motion graphs, rigs
- `.mtar`/`.gani`, `.mog` motion graph, `.frig`/`.frdv` rigs, motion events.
- **Gate:** sampled poses equal live captured bone transforms for reference clips.
- Note (2026-10-21, community): youarebritish (FoxKit / FoxEngineTemplates author) says **motion graphs (`.mog`) are among the least understood Fox formats** — a realistic, valuable target where this project can contribute new knowledge. Milestone scope unchanged.

## M8 Gameplay core [PLANNED] — Player, Soldier AI, SendCommand handlers, damage (headless)
- GameObject families Player2 and Soldier2, AI framework (node tables, blackboard), SendCommand handlers, damage. Headless.
- **Gate:** per system, behaviour fixtures (state sequences) reproduced.

## M9 Gameplay extended [PLANNED] — sound, bosses, UI
- Sound (Wwise containers, `.sdf`/`.sbp`), bosses (Sahelan2; `docs\SAHELAN.md` is the deepest spec), UI.
- **Gate:** per system, behaviour fixtures (state sequences) reproduced.

## M10 Assets & rendering [PLANNED] — renderer and viewer last
- Materials/shaders, renderer + viewer (D3D11 or Vulkan, ImGui via vcpkg). Asset **decoding** (`.ftex/.ftexs`, `.fmdl`, `.fv2`/fova, `.parts`, `.geom`) moves into whichever milestone first needs it (e.g. `.geom` in M6, `.parts` in M8).
- **Gate:** all textures/models decode; RenderDoc captures of reference frames vs engine frames (per-pass image diff within tolerance).

## M11 Playable slice [PLANNED] — one free-roam area, player + one AI type
- One free-roam area streamed in, player controllable (KB+M), one AI type alive.
- **Gate:** scripted 60 s input replay produces the same state trace as the live game within tolerance.

## Parked track: Option B mod (Sahelanthropus pilot) — parked until the Mod checkpoint after M5 (Luc, 2026-10-22)
Feature-complete pending Luc's playtests (`STATUS.md`); resumes at the **Mod checkpoint** above. Its RE (`docs\SAHELAN.md`, `docs\PROBES.md`) feeds M8/M9.

---
<small>Source: `docs/ROADMAP.md` in the project repository &middot; generated 2026-10-24.</small>
