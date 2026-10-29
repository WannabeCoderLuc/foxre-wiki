# Roadmap

Goal: an engine in `Engine\` that loads the player's own MGSV:TPP 1.0.15.4 data and reproduces its behaviour, written from specs (`docs\formats\`, `docs\engine\`), never from copied game code or assets. Every milestone ends on a **machine-decidable gate** (lesson from awesome-rea, [`docs\TOOLING.md`](../library/tooling.md)); a milestone is done only when `engine_verify` is green for its gate tests.

Status keys: PASS = gate passed · IN PROGRESS · NEXT (the milestone to start next) · PLANNED. Update this file when a gate passes.

**Principles:** headless first (renderer last); every gate is checked against live traces; formats are decoded when a milestone first needs them. Order re-agreed with Luc 2026-10-22 (new M5 Resources & mission load) and re-cut 2026-10-29 by dependency and feasibility ("Order from M6 on" below).

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
| `.sdf`/`.sbp` sound packages (container only) | — | listed + byte-extract — moved to M12 (sound) |

Remaining M1 polish: texture name gap (FOX2 name resolution reported 2026-10-29: 100 % of classes and properties, 293,035/293,036 values from the files' own string tables) (22.8k unnamed `.ftexs`), exe-side parser VAs (all [?]).
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

## M4 Script host [PASS] (gate passed 2026-10-29, accepted by Luc) — Lua 5.1 + Fox/Tpp API
- Spec [`docs\engine\ScriptHost.md`](../engine/script-host.md) (2026-10-22): Lua runtime = stock 5.1 except TString chars behind a pointer [V]; live boot capture (FoxTrace 2): 170-chunk boot order, 147 library registrations, identical over 2 runs → `Engine\tests\fixtures\m4_lua_boot.json`.
- [x] Native binding map (2026-10-22): 4 registration paths (luaI_openlib, Fox table builder, Fox class tables, direct setfield) [V]; 399 libraries / 5,532 bindings / 2,286 enum values, 2 identical runs + static oracle → `Engine\tests\fixtures\m4_lua_bindings.json`, `test_m4_bindings.py`.
- [x] C side of chunk loading (Fox dofile, 0x1B/0x1C decode, boot coroutine, Script.LoadLibrary*) and per-frame C → Lua callers (OnUpdate, ScriptUpdater, OnSynchronizeSVars) [V].
- [x] Host boot (2026-10-22): `Engine\script\` runs init.lua + Tpp/start.lua (coroutine per frame) with no error; 108 chunks in the exact live order up to the mission load; static plain-value constants (`m4_lua_consts.json`).
- Lua 5.1 host (lupa prototype → embedded), the Fox/Tpp/GameObject API surface (264 native bindings, 2,433 used API functions in `mgsv_query_knowledge(lua_api)`), StrCode in Lua.
- [x] Record/replay started (2026-10-23): FoxTrace 3 `luaret` (thunk + direct `lua_CFunction` return recorder), 2 captures x 2 identical runs -> `m4_lua_returns.json` (536 names, 534 stable); host replay answers 89.1 % of the API the M5 scenario touches (6.4 % without) and the f30010 `OnAllocate`/`OnInitialize` finish (`test_m4_replay.py`). Open: table-valued natives (svars declarations), 48 remaining stubs, API call-log comparison.
- [x] Timers + message delivery (2026-10-28, gate a): mission bucket listener 0x140A1D7D0 decoded (`OnMessage(subScripts, sender, messageId, arg0..3)`, result 1 = resend, `Mission.GetCurrentMessageResendCount`), `GkEventTimerManager` Start/Stop/StopAll/IsTimerActive (`Engine/runtime/timers.py`); the init mission's title flow runs from its own `Timer.Finish` and matches live for 7 sequence transitions up to the autosave popup (`test_m4_messages.py`).
- [x] UI popups (2026-10-28, gate a part 2): popup UI state machine 0x140898500 sends `UI.PopupClose(id, selection)` when the close animation ends, `ErasePopup` = request flag [V static], 12-frame close [V live] (`Engine/runtime/popups.py`); `SignIn.Is*` = true, `GetScriptVersionFromSlot` from the save image. Host title flow runs by itself to `Seq_Demo_LogInKonamiServer` (10 live transitions, its own `ChangeLanguage` calls, Timer/UI order = live except IH's skipped autosave popup and the undecoded `UI.RequestPlayRecordClearInfo`); `test_m5_mission_load.py` uses it (58/58 kept), hand-driven from LogInKonamiServer. Open: Konami login / DLC / title-menu messages, `RequestPlayRecordClearInfo` raiser.
- [x] Login, DLC, pre-title (2026-10-28, gate a part 3): Konami login decoded (StartLogin command 0x1407D74A0, state machine 0x1407DEE70, Network.StartLogin/EndLogin raisers 0x14091C470/0x1407D50A0, live popups = `system_3200_all` ×2 / `system_3201_all`), pre-title UI 0x14085C8C0 state 4 → Lua `TppVarInit.StartTitle` [V static] (`Engine/runtime/online.py`). Host walks the 24 live transitions to `Seq_Demo_ShowKonamiAndFoxLogo` and loads title 40010 itself; m5 test hand-driven only from title CONTINUE (58/58 kept). Open: title-menu messages — blocked by 40010's DataIdentifier locator (M6).
- [x] Gate b call-log comparison (2026-10-29): FoxTrace logs table results (Lua 5.1 Table layout [V]); capture `trace_m4b_luaret_f30020_20261029_002259` (574 hooks = every binding the host calls); the host follows the live save (title 40020 → f30020), runs free roam with message delivery to `Seq_Game_FreePlay` against recorded natives (only error: M6 locator); call log vs live: 548 functions both sides, 517 same argument lists, first-call order 0.947, every one-sided function explained (`test_m4_gate_b.py`, ScriptHost.md "M4 gate b"). Open: 31 argument-list differences (save / IH quest pick / title boundary), E29 `pairs` insertion order, title menu (M6).
- **Gate (re-agreed 2026-10-22):** init + f30010 mission scripts run against **recorded** native return values (record/replay fixture from a live capture); chunk order and API call log match the live capture. (Dropped: "no unstubbed API calls"; natives are answered from the replay fixture.)
- **State (2026-10-29):** met for the init mission and free roam (f30010 and f30020 saves) up to the differences listed in `ScriptHost.md` "M4 gate b". The title menu belongs to M6 (it waits for the locator lookup) and moved into M6's gate. **Gate passed (Luc, 2026-10-29)** with those differences recorded as open items (E14, E29).

## M5 Resources & mission load [PASS] — packs, blocks, async resources, mission start
- Pack/block system, async resource requests, the mission load flow (`start2nd.lua` / `TppMission` / block groups), pack-scoped VFS (mission scripts become visible only once their pack is loaded). Spec [`docs\engine\Resources.md`](../engine/resources.md).
- [x] Mission load decoded (2026-10-23, [`docs\engine\Resources.md`](../engine/resources.md)): `Mission.LoadLocation/LoadMission` latch requests; location loader + mission block controller (vtable 0x1422A9710, from `TppSimpleMissionBlockControllerData`) ask the Lua package-path functions; `.lua` entries of loaded packages are script resources (reverse entry order); `OnAllocate`/`OnInitialize` coroutines; `mvars` reset by the mission object [V].
- [x] `Engine\resources\` (loader, FSTB common-package header) + pack-scoped `Engine\script\vfs.py`: host loads **46 chunks in the exact live order** from live chunk 112 (init → title 40010 → f30010, minus 9 UI tables), block events match (`test_m5_mission_load.py`).
- [x] Script blocks (2026-10-23): 8-slot system decoded (`ScriptBlock.*`, slot update 0x140184340, OnAllocate/OnInitialize/OnUpdate/OnTerminate) → `Engine\resources\blocks.py`; svars change log → `OnChangeSVars`, mission `OnUpdate`, save boundary `LoadVarsFromSlot` (live save image), 2nd luaret capture (663 natives) + IH Lua trace. Host loads **49/49 chunks from live 112 to the end of the boot** (UI tables excluded), script blocks quest / reinforce / animal in vanilla order, slots and `ScriptBlock.Load` calls as live (`test_m5_mission_load.py`, `test_m5_script_blocks.py`). Live tail order differs only by IH's patched `f30010.fpkd` [V].
- [x] UI parameter tables (2026-10-24): the `mbdvc_*` tables are `mb_dvc_top.fpk` scripts, reloaded by the iDroid on every `TppUiCommand.ChangeLanguage()` (3 per boot: TppUiBootInit, init_sequence SetSavedLanguage, CreateOrLoadSaveData), `emblem_list.lua` from the emblem setup 0x1405CF950 [V static + live capture `trace_m5_lang`] → `Engine\resources\ui.py` (`IDroid`). Host boot: 112/112 live chunks (boot UI load asserted as an async group: live order varies between runs); M5 scenario: **58/58 live chunks from 112** (the title flow's language changes and loads at the native boundary).
- **Gate passed (2026-10-24):** chunk + block event order from live chunk 112 to the end of the boot (`m4_lua_boot.json` chunks 112–169) reproduced by the host.

## Order from M6 on (re-cut 2026-10-29)
The old M6 World bundled three different kinds of work (world streaming, two file formats, the navigation runtime) and the old M10 bundled offline asset decoding with the renderer. From M6 on, the milestones are cut so that each one depends only on milestones before it, and the next one is always the most feasible with what exists:

| Order | Milestone | Depends on | Why here (feasibility) |
|---|---|---|---|
| **M6** | World streaming & locators | M2 entities, M4 host, M5 loader | The host already stops here (the title's `DataIdentifier` locator; title menu and CONTINUE still hand-driven); live signals (`Block.*` messages) are in every capture; open items E20–E22 are narrow. Closes M4's residue. |
| M7 | Terrain & collision formats | M1 containers, M6 block grids | Pure format work, offline, same proven pattern as M1 (census → spec → byte-identical codec). Gives the ground and collision that navigation and gameplay sample. |
| M8 | Navigation & routes | M6, M7, M1 `.nav2`/`.frt` codecs | Codecs exist; the runtime has verified RE (`BATTLEFIELD.md` §4, `SAHELAN.md` navigation, probe goal logs). Path queries need the streamed world and the ground. |
| M9 | Gameplay core (headless) | M3, M4, M6–M8 | Soldier AI, CP / notice, damage and SendCommand handlers act in a world with paths; the richest RE already exists (`BATTLEFIELD.md`, `SAHELAN.md` §9–§10, the knowledge DB's 514 command handlers). |
| M10 | Asset formats | M1 | Offline decoding (`.ftex/.ftexs`, `.fmdl`, `.frig/.frdv`, `.fv2`/fova, `.parts`, `.lng`): independent, but nothing before M11 needs it, so it sits where animation needs rigs and models. |
| M11 | Animation | M10 rigs / models, M9 states | `.mtar`/`.gani` clips, the `.mog` motion graph (least understood Fox format: new knowledge), motion events. Needs skeletons from M10 and character states from M9. |
| M12 | Gameplay extended | M9, M11 | Sound (`.sdf`/`.sbp`, Wwise), bosses (TppSahelan2: `SAHELAN.md` is the deepest spec), UI / iDroid logic. |
| M13 | Rendering & viewer | M7, M10, M11 | Renderer last, by principle; needs terrain, models, textures and poses. First risk to clear early: a RenderDoc capture of the game (untested with Denuvo). |
| M14 | Playable slice | all | One free-roam area, player + one AI type. |

Old → new numbers (older docs, the log and test names keep the old ones): M6 World → **M6** streaming & locators + **M7** terrain & collision + **M8** navigation & routes · M7 Animation → **M11** · M8 Gameplay core → **M9** · M9 Gameplay extended → **M12** · M10 Assets & rendering → **M10** asset formats + **M13** rendering · M11 Playable slice → **M14**.

## M6 World streaming & locators [NEXT] — stage blocks, location loader, locators
- Stage-block controller and the large / small / LOD block grids around the player (`StageBlockControllerData`, `Block.OnChangeLargeBlockState`, `StageBlockCurrentSmallBlockIndexUpdated`), location loader update and frame order (E21), mission controller block state 4 and the two Quark services (E20), FSTB tables beyond the header (E22).
- Locators: `DataIdentifier` / `GetDataWithIdentifier`, locator lookups by name and by transform (`Tpp.GetLocatorByTransform`), `.lba` locator files (footer pairs already decoded for `Fox.PathFileNameCode32`).
- Takes over from M4: the title heli space's `OnAllocate` (`heli_common_sequence.OnBuddyBlockLoad` → `HelispaceLocatorIdentifier` / `BuddyDDogLocator`), so the title sequence, the title-menu messages (`UI.TitleMenuReady`, `EndFadeIn`, `TitleMenu(PressStart, Continue)`) and a real CONTINUE run in the host.
- Spec [`docs\engine\World.md`](../engine/world.md) (new), module `Engine\world\`. Skills `fox-system`, `fox-ground-truth`, `fox-engine-module`.
- [x] Locators (2026-10-29): DataIdentifier registry + lookup decoded (0x14017F170 / 0x14017EDD0, registry 0x142B72A88) and implemented over the mounted DataSets (`Engine/world/identifiers.py`); the title's `HelispaceLocatorIdentifier` lookups match live for both saves, 40010 / 40020 finish OnAllocate + OnInitialize with no Lua error (`test_m6_world.py`). `World.md` first draft.
- [ ] Stage blocks: live Block.* fixture (`m6_block_messages.json`, 2 saves × 2 runs), FSTB large-block prefix decoded (name = StrCode32 of the pack_large stem, box `x | y<<16`); controller (small-block index, activation rule, raise sites) and host emission open.
- [ ] Title menu + the game's own CONTINUE.
- **Gate:** for both recorded saves (f30010 afgh, f30020 mafr) the host's stage-block messages match a live fixture for the boot → free-roam span; the title's locator lookups resolve; the title menu runs and `Engine\script\scenario.py` reaches free roam through the game's own CONTINUE (no hand-driven load).

## M7 Terrain & collision formats [PLANNED] — `.htre`/`.tre2`, `.geom`
- Census → spec → byte-identical reader/writer on every game file (`fox-format`), like M1. `.geom` also closes the `*_PhysicsData` entities left open since M2 (E7). Leads only: 010 templates `htre.bt`, `geom_geoms_gskl.bt`.
- **Gate:** every terrain and collision file round-trips byte-identical; heightmap samples equal live ground heights at recorded points (fixture from the IH pipe).

## M8 Navigation & routes [PLANNED] — nav2 runtime, route following
- Portal-graph path search over `.nav2`, `TppNavigationController` snap / plan, nav worlds; `.frt` route following and route events (E6: 35 unnamed event types). Evidence: `BATTLEFIELD.md` §4, `SAHELAN.md` (navigation), probe goal logs.
- **Gate:** path queries equal live `RequestMove` results (fixtures); a soldier's route-following state sequence matches live.

## M9 Gameplay core [PLANNED] — Soldier AI, CP / notice, damage, SendCommand handlers (headless)
- GameObject families Soldier2 and Player2 (state, not animation), AI framework (node tables, blackboard), CP phase and notice, damage, SendCommand handlers. Evidence: `BATTLEFIELD.md`, `SAHELAN.md` §9–§10, `structs_soldier\`, the knowledge DB's command handlers.
- **Gate:** per system, behaviour fixtures (state sequences) reproduced.

## M10 Asset formats [PLANNED] — textures, models, rigs, fova, parts, language
- `.ftex/.ftexs`, `.fmdl`, `.frig/.frdv`, `.fv2`/fova, `.parts`, `.lng`: decode (and re-encode where the format allows) on every game file; texture path recovery from `.fmdl`/`.mtar` strings (E2, 22.8k unnamed textures).
- **Gate:** every file of each format decodes; byte-identical round trip where the format allows; decoded textures match an independent decoder.

## M11 Animation [PLANNED] — clips, motion graphs, motion events
- `.mtar`/`.gani` clips, the `.mog` motion graph, motion events. Note (2026-10-21, community): youarebritish (FoxKit / FoxEngineTemplates author) says **motion graphs (`.mog`) are among the least understood Fox formats**, a realistic target where this project can add new knowledge.
- **Gate:** sampled poses equal live captured bone transforms for reference clips.

## M12 Gameplay extended [PLANNED] — sound, bosses, UI
- Sound (Wwise containers, `.sdf`/`.sbp`), bosses (TppSahelan2: `docs\SAHELAN.md` is the deepest spec), UI / iDroid logic.
- **Gate:** per system, behaviour fixtures (state sequences) reproduced.

## M13 Rendering & viewer [PLANNED] — renderer last
- Materials / shaders, renderer + viewer (D3D11 or Vulkan, ImGui via vcpkg).
- **Gate:** RenderDoc captures of reference frames vs engine frames (per-pass image diff within tolerance). Early risk check (any time): one RenderDoc capture of the game with plugins removed.

## M14 Playable slice [PLANNED] — one free-roam area, player + one AI type
- One free-roam area streamed in, player controllable (KB+M), one AI type alive.
- **Gate:** scripted 60 s input replay produces the same state trace as the live game within tolerance.

## Retired
- **Mod checkpoint and Option B mod (Sahelanthropus pilot)**, dropped 2026-10-28 (Luc): no mod work, deliverables or playtests. History in [`docs\LOG.md`](log.md); the verified RE (`docs\SAHELAN.md`, `docs\PROBES.md`, `docs\BATTLEFIELD.md`) is evidence for M8, M9 and M12.

---
<small>Source: `docs/ROADMAP.md` in the project repository &middot; generated 2026-10-29.</small>
