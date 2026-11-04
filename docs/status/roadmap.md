# Roadmap

Goal: an engine in `Engine\` that loads the player's own MGSV:TPP 1.0.15.4 data and reproduces its behaviour, written from specs (`docs\formats\`, `docs\engine\`), never from copied game code or assets. Every milestone ends on a **machine-decidable gate** (lesson from awesome-rea, [`docs\TOOLING.md`](../library/tooling.md)); a milestone is done only when `engine_verify` is green for its gate tests.

Status keys: PASS = gate passed · IN PROGRESS · NEXT (the milestone to start next) · PLANNED. Update this file when a gate passes.

**Principles:** headless first (renderer last); every gate is checked against live traces; formats are decoded when a milestone first needs them. Order re-agreed with Luc 2026-10-22 (new M5 Resources & mission load) and re-cut 2026-10-29 by dependency and feasibility ("Order from M6 on" below), and re-cut again 2026-11-04 by feasibility with the engine as a mod platform ("Order from M10 on", "Standing rules", "Common gate" below). Machine-readable gate list: `Engine\tests\gates.json` (`engine_verify(gate="Mxx")`).

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
| ~~M10~~ | Asset formats (now M11) | M1 | Offline decoding (`.ftex/.ftexs`, `.fmdl`, `.frig/.frdv`, `.fv2`/fova, `.parts`, `.lng`): independent, but nothing before M11 needs it, so it sits where animation needs rigs and models. |
| M11 | Animation | M10 rigs / models, M9 states | `.mtar`/`.gani` clips, the `.mog` motion graph (least understood Fox format: new knowledge), motion events. Needs skeletons from M10 and character states from M9. |
| M12 | Gameplay extended | M9, M11 | Sound (`.sdf`/`.sbp`, Wwise), bosses (TppSahelan2: `SAHELAN.md` is the deepest spec), UI / iDroid logic. |
| M13 | Rendering & viewer | M7, M10, M11 | Renderer last, by principle; needs terrain, models, textures and poses. First risk to clear early: a RenderDoc capture of the game (untested with Denuvo). |
| M14 | Playable slice | all | One free-roam area, player + one AI type. |

Old → new numbers (older docs, the log and test names keep the old ones): M6 World → **M6** streaming & locators + **M7** terrain & collision + **M8** navigation & routes · M7 Animation → **M11** · M8 Gameplay core → **M9** · M9 Gameplay extended → **M12** · M10 Assets & rendering → **M10** asset formats + **M13** rendering · M11 Playable slice → **M14**.

## Order from M10 on (re-cut 2026-11-04, Luc: engine as mod platform, ordered by feasibility)
Supersedes the M10-M14 rows above. M9 is unchanged (in progress). Three changes: (1) the engine becomes a **mod platform** (in-engine Mod API; mod tooling for the original game is the separate, scope-gated MOD-A); (2) gaps closed: **physics / character controller** (no milestone had it) and **real native implementations** (M4 passed on recorded natives); (3) the path from one area to the whole offline game.

**Feasibility rule:** next is always the milestone with the least new RE risk given what exists. Engineering on passed milestones first (M10), offline format work next (M11), then systems that sit on the already-recorded Lua / native boundary (M12, M13), then new runtime RE (M14-M16), integration headless (M17), content breadth (M18-M19), and the outputs last: drawing (M20), sound playback (M21), playable game (M22), standalone runtime (M23), API freeze (M24). Each milestone depends only on milestones before it.

| Order | Milestone | Depends on | Why here (feasibility) |
|---|---|---|---|
| M9 | Gameplay core (headless) | M3-M8 | PASS (Luc, 2026-11-04). |
| **M10** | Mod API core (headless) | M2-M9 | No new RE and no live captures: registries, manifest, loader, sandbox and hooks over nine passed milestones. Fixes the extension points before more systems are built. |
| M11 | Asset formats (+ sound containers) | M1, M10 | Offline, the proven M1 / M7 pattern (census → spec → byte-identical codec); community templates exist (FtexTool, `fmdl.bt`, `frig.bt`). Writers feed the mod importers. |
| M12 | Sound & UI logic (headless) | M4, M5, M9, M11 | Both live at the Lua / native boundary M4 already records (`TppSoundDaemon.PostEvent`, `TppUiCommand`, popups, title flow). Events and states only; playback is M21, drawing M20. |
| M13 | Open world complete (headless) | M6, M7, M8, M12 | Extends the passed M6 streaming to both maps and every block level; clock and weather are Lua-visible; the game's random generator (needed for determinism everywhere after) is a contained static-RE target with an emulator oracle. |
| M14 | Collision & physics | M7, M9, M13 | New runtime RE but bounded: typed shape trees (E30), queries the game itself makes (FoxTrace-capturable), character controller fed with recorded root motion until M16. |
| M15 | Combat & equipment (headless) | M9, M13, M14 | Equip tables are data; ballistics and hits need M14 collision and M13 random numbers; the M9 capture protocol already handles combat runs. |
| M16 | Animation | M11, M14, M15 | Hardest format (`.mog`, least understood) and live bone captures; comes after physics and combat so it replaces recorded root motion and timings in a running system. |
| M17 | Headless slice | M10-M16 | First integration: one area, player + one AI type, 60 s input replay, **zero recorded natives**. No renderer needed. |
| M18 | Full cast | M17 | Breadth: every soldier type, animals, buddies, heli, vehicles, bosses, each as a content pack on the Mod API. |
| M19 | Missions & progression | M18 | Needs the full cast and both maps; mission Lua already runs in the host. |
| M20 | Rendering (reference) | M11, M13, M16 | Renderer last, by principle; biggest unknown (RenderDoc vs Denuvo untested). Early risk check allowed any time. |
| M21 | Audio output | M11, M12 | Wwise-compatible playback; third-party codec and mixing behaviour, independent of drawing. |
| M22 | Playable game | M17-M21 | Rendering + audio + input on the verified headless game. |
| M23 | Standalone runtime | M22 | Performance and packaging last. |
| M24 | Mod platform 1.0 | M23 | API freeze once the whole engine exists; 0.x versions from M10 on. |

Old → new numbers (2026-11-04; older docs and the log keep the old ones): M10 Asset formats → **M11** (+ sound containers) · M11 Animation → **M16** (physics split out as **M14**) · M12 Gameplay extended → **M12** sound & UI logic + **M18** bosses + **M21** audio output · M13 Rendering → **M20** · M14 Playable slice → **M17** headless slice + **M22** playable game. New: **M10** Mod API core, **M13** open world, **M15** combat, **M19** missions, **M23** standalone, **M24** mod platform 1.0, mod track MOD-A to MOD-E (MOD-A out of scope for now, Luc 2026-11-04).

## Standing rules (Luc, 2026-11-04; apply to M9 onward)
- **Natives are ported by the milestone that owns them.** Each binding in `Engine\tests\fixtures\natives_owner.json` (to be created in M10 from `m4_lua_bindings.json`) names its owning milestone; that milestone implements it, switches its recording off and keeps a call-log test (`impl == live`). M17 runs with zero recorded natives.
- **Extension points in every spec.** Each `docs\engine\*.md` / `docs\formats\*.md` has an "Extension points" section: what a mod can register, override, hook or replace, through which API.
- **Data-driven registries.** GameObject types, SendCommand handlers, message ids, updaters, AI node tables, resource loaders, reflection classes and Lua libraries are registered, never hardcoded; vanilla registers through the same path as mods and behaves exactly like the original.
- **Determinism.** Randomness only from the engine's seeded generator (the game's own generator once M13 decodes it); fixed frame order from the scheduler.
- **Compat mode.** With no mods loaded every vanilla gate passes; enhanced features are separate modes and never weaken a vanilla gate.
- **Gate registry.** Every gate item is listed in `Engine\tests\gates.json` with the tests that decide it; `engine_verify(gate="M10")` reports each item PASS / FAIL / NOT BUILT. A milestone passes when every item is PASS and Luc accepts it.

## Common gate (every milestone from M10 on, in addition to its own items)
- **C1 Suite:** full `engine_verify` (slow verifiers included) PASS; verifier lock unchanged or relocked after review.
- **C2 Specs:** every system / format the milestone touches has a spec with "Extension points" and "Evidence" sections (`test_docs_contract.py`).
- **C3 Natives:** every binding the milestone owns is implemented, not answered from a recording, and its call log equals live (`test_natives_owned.py`).
- **C4 Determinism:** the milestone's scenario run twice with the same seed gives byte-identical traces.
- **C5 Fixtures:** each live fixture comes from at least two runs that agree, or the varying values are pinned as ranges with the reason in the spec; clamped and free runs never mixed (M9 capture protocol).
- **C6 Mods:** each new extension point has a reference mod under `Engine\mods\reference\` passing its own fixtures; all vanilla items pass with no mod and with the null mod loaded.
- **C7 Native backends:** where a C++ backend exists, `cpp == py` on the milestone's fixtures.
- **C8 Docs:** hand-written site pages for the milestone rewritten; `sync_wiki.py` builds with `mkdocs build --strict`.

## Implementation language & native boundary (Luc, 2026-10-29)
- **Python first through M8:** M7 (`.htre`/`.tre2`/`.geom`) and M8 (`.nav2`) codecs and spatial queries are pure Python. Python stays the permanent reference implementation.
- **Targeted C++ from M9 via `pybind11`:** only hot runtime query paths (height sampling, collision / raycast queries, nav pathfinding) move to C++, each checked by a differential pytest oracle against the Python version (`cpp_fn == py_fn`). Format codecs in `Engine\formats\` stay Python for good.
- **Guardrails in M7-M8:** spatial math in strict float32 (`numpy.float32` / `ctypes.c_float`) so results match the exe's 32-bit `xmm` math now and C++ `float` bit-for-bit later; byte-identical format codecs (`Engine\formats\`) are kept separate from runtime query objects (`Engine\world\`), which take contiguous buffers so a `pybind11` backend can drop in behind the same signatures.

## M6 World streaming & locators [PASS] — stage blocks, location loader, locators
- Stage-block controller and the large / small / LOD block grids around the player (`StageBlockControllerData`, `Block.OnChangeLargeBlockState`, `StageBlockCurrentSmallBlockIndexUpdated`), location loader update and frame order (E21), mission controller block state 4 and the two Quark services (E20), FSTB tables beyond the header (E22).
- Locators: `DataIdentifier` / `GetDataWithIdentifier`, locator lookups by name and by transform (`Tpp.GetLocatorByTransform`), `.lba` locator files (footer pairs already decoded for `Fox.PathFileNameCode32`).
- Takes over from M4: the title heli space's `OnAllocate` (`heli_common_sequence.OnBuddyBlockLoad` → `HelispaceLocatorIdentifier` / `BuddyDDogLocator`), so the title sequence, the title-menu messages (`UI.TitleMenuReady`, `EndFadeIn`, `TitleMenu(PressStart, Continue)`) and a real CONTINUE run in the host.
- Spec [`docs\engine\World.md`](../engine/world.md) (new), module `Engine\world\`. Skills `fox-system`, `fox-ground-truth`, `fox-engine-module`.
- [x] Locators (2026-10-29): DataIdentifier registry + lookup decoded (0x14017F170 / 0x14017EDD0, registry 0x142B72A88) and implemented over the mounted DataSets (`Engine/world/identifiers.py`); the title's `HelispaceLocatorIdentifier` lookups match live for both saves, 40010 / 40020 finish OnAllocate + OnInitialize with no Lua error (`test_m6_world.py`). `World.md` first draft.
- [x] Stage blocks (2026-10-29): controller decoded (update 0x1401611F0 / 0x140161500, raisers 0x140161816 / 0x140177870, position provider `StageBlockCurrentPositionSetter` fed from `vars.initialPlayerPos*`, window centre = centerIndex + floor(p / 128), sentinels ±1,000,000 = 7945 / 57857, large blocks from the FSTB small-block lists in the 5×5 window ± largeBlockLoadingMargin) and implemented (`Engine/world/stage_blocks.py`); host stage-block messages = live for f30010 and f30020 (`test_m6_world.py`).
- [x] Title menu + the game's own CONTINUE (2026-10-29): raisers decoded (pre-title / title-menu sequence 0x14085C8C0 states 6-14 raise `UI.TitleMenu`, fade-end raiser 0x14092CC60 raises `EndFadeIn` / `EndFadeOut` after FoxFadeIo's timed fade, splash screens 0x14090E690 ff., loading-tips end 0x14089A700) and implemented (`Engine/runtime/title.py`); `scenario.py` reaches free roam for f30010 and f30020 through the title script's own `OnEndFadeOutSelectContinue`; title-menu messages = live order (`test_m6_world.py`). Open: TitleMenuReady / RequestPlayRecordClearInfo raisers (obfuscated code) [?].
- **Gate:** for both recorded saves (f30010 afgh, f30020 mafr) the host's stage-block messages match a live fixture for the boot → free-roam span; the title's locator lookups resolve; the title menu runs and `Engine\script\scenario.py` reaches free roam through the game's own CONTINUE (no hand-driven load).
- **State (2026-10-29):** all three gate items met for both saves (`test_m6_world.py`, quick suite 81/81); **Gate passed (Luc, 2026-10-29).** Open items stay recorded (E20-E22, TitleMenuReady raiser).

## M7 Terrain & collision formats [PASS 2026-10-29] — `.htre`/`.tre2`, `.geom`
- Census → spec → byte-identical reader/writer on every game file (`fox-format`), like M1. Leads only: 010 templates `htre.bt`, `geom_geoms_gskl.bt`.
- [x] FoxData container (2026-10-29): all five types are one node-tree format ([`docs/formats/FOXDATA.md`](../formats/foxdata.md), `Engine/formats/foxdata.py`); node / parameter layout [V] from the exe readers (0x1401A5C10, 0x1401A5D00, 0x1401FB4B0); **9,340 / 9,340 unique files byte-identical** (`test_foxdata_all.py`).
- [x] Terrain typed (2026-10-29): `.htre` v3 / v4 + `.tre2` ([`docs/formats/HTRE.md`](../formats/htre.md), `Engine/formats/terrain.py`); loaders 0x1401F95B0 → HTRE 0x1401FA490 / TRE2 0x1401FADD0, patch reader 0x1401F9A90 [V]; **4,164 / 4,164 byte-identical, every v4 patch offset = its payload** (`test_terrain_all.py`); float32 `HeightField` query (`Engine/world/heightfield.py`).
- [x] Collision container (2026-10-29): `.geom` 3,078 / `.geoms` 2,033 / `.gskl` 65 byte-identical with zero undecoded bytes outside payloads; payload top layer [D] ([`docs/formats/GEOM.md`](../formats/geom.md)). Typed shape trees = E30.
- [x] E7 answered (2026-10-29): `*_PhysicsData` links live in `.ph` / `.sim` FOX2 DataSets, not `.geom`; resolved to the file's single `PhObjectDesc` (s10151 54 / 54, Entities.md "Physics data links").
- [x] Live ground-height fixture (2026-10-29, IH pipe warp-drops in f30010, `Memory/research/m7_ground_20261029_182058`): cluster-tiled heightMap, block origin ((b - 133) * 128), rows = z / columns = x, triangle pair split (x0,z0)-(x1,z1) [V live]; `HeightField.from_blocks` / `from_tre2`; 24 terrain points over 6 blocks = live within 5 mm (`test_m7_ground.py`, E31 answered).
- **Gate:** every terrain and collision file round-trips byte-identical (**met 2026-10-29**); heightmap samples equal live ground heights at recorded points (fixture from the IH pipe) (**met 2026-10-29**, `m7_ground_heights.json`). **Gate passed (Luc, 2026-10-29).** Open items stay recorded (E30, E32).

## M8 Navigation & routes [PASS] — nav2 runtime, path queries (Luc, 2026-11-01)
- Portal-graph path search over `.nav2`, `TppNavigationController` snap / plan, nav worlds; `.frt` route following and route events (E6: 35 unnamed event types). Evidence: `BATTLEFIELD.md` §4, `SAHELAN.md` (navigation), probe goal logs.
- [x] E6 narrowed (2026-10-30): `.frt` reader view 0x142187500, +0x2C unread by it, +16 event names, 19 types (1.33 %) left (`FRT.md`).
- [x] `.nav2` tiles use the M7 block origin, 779 / 779 (`NAVMESH.md`).
- [x] `Navigation.md` draft; request / path layout decoded; live fixture of real `RequestMove` paths (`m8_nav_paths.json`, FoxTrace `navreq`).
- [x] `Engine/world/navigation.py` + `test_m8_nav.py`: approximate only: 60 % of 410 requests within 0.1 m, 87 % within 1 m, worst 11.8 m.
- [x] Path job decoded and ported, six stages (`Navigation.md`); clean job fixture `m8_nav_jobs.json`: 863 of 883 within 0.1 m (2026-11-01).
- [x] Paths equal live (2026-11-01): 948 of 948 jobs within 0.1 m, xfail removed; runtime blocks, obstacle rings and dynamic links ported, fed from the recorded state; runs `m8_nav14`, `m8_nav15` (afgh free roam, sneak).
- [x] Edge events → speed class decoded and ported (2026-11-01, 0x140ED4C10); far soldiers 0.80 m/s on all walk events.
- [x] Far route following: far soldiers stay on route edges in node order (97 of 170 fit one route) at 0.80 m/s.
- Moved to M9 (Luc, 2026-11-01): state sequence near the player, far-mode switch, run and dash speeds. Getting close needs protection and belongs with the AI behaviour captures.
- **Gate (not met):** path queries equal live `RequestMove` results (fixtures); a soldier's route-following state sequence matches live.

## M9 Gameplay core [PASS, Luc 2026-11-04] — Soldier AI, CP / notice, damage, SendCommand handlers (headless)
- GameObject families Soldier2 and Player2 (state, not animation), AI framework (node tables, blackboard), CP phase and notice, damage, SendCommand handlers. Evidence: `BATTLEFIELD.md`, `SAHELAN.md` §9–§10, `structs_soldier\`, the knowledge DB's command handlers.
- **Live capture protocol first (Luc, 2026-11-01):** near soldiers the player must not die and runs must stay readable: unlimited health, recorded phase control, other measures confirmed to work, driver without combat input, unplanned events logged and the run marked. Clamped and free runs are never mixed in a fixture.
- [x] Capture protocol written and proven (2026-11-01, `engine\SoldierAI.md`): 45 hits under alert with life unchanged, driver stops on hand input, phase rise, damage in free runs. Sight and hearing scale not confirmed, so not used.
- [x] Route step machine (2026-11-01, `route_follow.py`, `test_m9_route.py`, runs `m9_route1`, `m9_route2`): one `RequestMove` per leg start (0x1415713C0), slot = soldier index [V]; leg and node event order equals live on all 1,662 changes of both runs; waits = event time in frames.
- [x] Known target over two runs (2026-11-01, `m9_known1`, `m9_known2`): notice, alert, evasion, caution order, other CPs, target leaves its route. Phase lengths vary between runs, so only the order is pinned.
- [x] CP phase timers decoded statically (2026-11-01, `engine\SoldierAI.md`): normalized timer, base rates caution 1/2160, evasion 1/120, alert 1/30, alert multipliers. Not read live, evasion not explained, not ported.
- [x] CP phase lengths read live and pinned (2026-11-04, `cp_phase.py`, `test_m9_phase.py`, runs `m9_phase1`, `m9_phase2`, FoxTrace 3.1 `cpphase` + `notice`): rates live, drain float32 bit-exact at x1; a phase falls back when a CP request finishes (alert 0x3C then 0x3B, evasion 0x3A), not on the timer; both runs agree (alert 60.8 s past leaving, evasion 3684 frames). Notice by sight from soldier 81 alone.
- [x] Third step, rest (2026-11-04, `test_m9_radio.py`, runs `m9_phase3`, `m9_phase4`, FoxTrace 3.2; names from the dev-build map `GeminiWork\decomp\mgsv.db`, bodies read): request ids are radio types spoken by members; the alert 21 s = soldier 81's investigate role (1264 frames both runs, record +4 bit 7 = `CheckActiveMember`), 0x3A = the investigator's own report (`InvestigateAiImpl` step 10, literal 0x3A), so evasion lasts as long as the investigation. Unrealized speeds decoded (`GetMoveVelocityForUnreal` 0x14139D600, port `realize.unreal_move_speed`). Sight scale 0: no notice at 3.5 m; 100: soldier 81 by sight 0.52 s, alert 4.6 s (one run each).
- [x] G5 second base (2026-11-04, `test_m9_g5.py`, runs `m9_eb1`, `m9_eb2` at afgh_enemyBase_cp, lone patrol soldier 6, FoxTrace 3.3): alert -> evasion -> caution with the same radio chain; investigators given by `UpdateFrontLineInAlert` (3), alert state 2 (2), evasion (4); **the investigate role ends when the CP's search point is completed** (`Controller_CompleteInvestigation_` 0x140D57260 clears point bit 0x40; role update 0x140D7BBE0 drops the role, 0x3B the same frame); radio length = voice line playback (`RadioControllerImpl::StepRadio` waits on the voice player), measured per type (0x3C / 0x3B 147, 0x51 ~687, 0x53 ~622, 0x3A 95 to 178 frames by speaker). Port `cp_phase.role_holds`, `complete_investigation`.
- [x] **G6 alert slow band point (2026-11-04):** impl +0x5D8 is the alert's front point, written by `UpdateCpAtHost` 0x140D65850: a seen player's position when it is more than 10 m from the point (1 s linger after sight is lost); the band applies while the player stays within 10 m of it. Ported (`cp_phase.front_point_update`, `linger`, `near_point`, `alert_drain_step`), pinned on runs `m9_g6d`, `m9_g6f` (band on by the 10 m test alone, x0.01), `m9_g6e` (band on, bit 7 also set) and `m9_g6b`, `m9_g6c` (no band); gate M9 6/6 PASS, for Luc's review, `test_m9_g6.py`.
- **Gate accepted by Luc (2026-11-04): G1-G6 PASS.** Damage and SendCommand handlers beyond phase control were not gate items: damage moves to M15 Combat, the handler set to the M10 registries.
- [ ] Leftovers (not gate items): evasion x0.025 stretch; flag bits -> unrealized (phase, speed) live; +0x1A0 byte, view test, slot swaps in the realize port; hearing.
- [x] Far-mode switch decoded (2026-11-01): realize budget 18 inside the stage window, 32 m in / 28 m out, 0x141551820; `Engine\world\realize.py`, 159 of 181 live lists equal, the rest within sample age.
- [x] Run and dash speeds measured (2026-11-01): realized 2.50, 4.01, 6.43; unrealized 2.00, 2.75, 4.00.
- [x] Route state decoded (2026-11-01): impl +0xE8 route + state; 3 -> 2 <-> 1, 3 -> 0 -> 1 pinned.
- [x] **G4 route following near the player (E33)** (2026-11-04, `route_follow.py`, `test_m9_g4.py`, runs `m9_g4b`, `m9_g4c`, FoxTrace 3.4 `idleact`): steps 4 / 5 = board / leave vehicle or walker gear, 0x10 = route ended [V]; foot arrival = remaining path < 0.25 m, walker gear < 1.0 m [V]; same spot = |soldier - next node|^2 < 1.0 after the last event [V 0x14156B120]; order equals live on 945 / 947 changes. Long waits explained: action-mode events end when `IdleActingActionImpl` ends; its time counts only in StandIdle and freezes during random single actions (up to 18 s), so wait = time + single actions [V, D on 173 events].
- [x] First behaviour fixture (2026-11-01): caution route switch, evasion fallback after about 26 s (`m9_soldier_forced.json`, two runs).
- [x] Soldier behaviour by phase: evasion, alert with a known target as state sequences; a second base (G5, 2026-11-04).
- **Gate:** per system, behaviour fixtures (state sequences) reproduced.

## M10 Mod API core [PLANNED, next] — registries, manifest, loader, hooks (headless)
- Data-driven registries for everything M2-M9 built: GameObject types, SendCommand handlers, message ids, updaters (phase + priority), AI node tables, resource loaders, reflection classes, Lua libraries. Vanilla registered through the same path.
- Mod manifest (namespace, API version 0.x, dependencies, load order); loader with conflict detection; Lua mods in the `lua51_run` sandbox pattern; Python mods for prototypes.
- Extension kinds: new system (updater + lifecycle `OnAllocate / OnInitialize / OnUpdate / OnTerminate`), message listeners and own message ids (namespaced StrCode32), new GameObject types with handlers, new `.fox2` classes, parameter overrides (layered by load order), before / after hooks (observe, change, cancel), SendCommand handler chaining, AI node insert / replace, blackboard access, Lua libraries.
- `natives_owner.json`: every binding from `m4_lua_bindings.json` assigned to its owning milestone.
- "Extension points" back-filled into `Entities.md`, `Scheduler.md`, `Messages.md`, `ScriptHost.md`, `Resources.md`, `World.md`, `Navigation.md`, `SoldierAI.md`. Spec `docs\engine\ModAPI.md`, module `Engine\mods\`.
- **Gate:**
  - G1 Registries: every type, handler, message, updater and Lua library the engine implements is registered through the registry; the registry dump equals the previous hardcoded tables; every M0-M9 gate test passes unchanged (`test_m10_registry.py`).
  - G2 Null mod: full suite with the null mod loaded gives byte-identical traces to no mod (`test_m10_null_mod.py`).
  - G3 Reference mods, one per extension kind, each with a fixture (`test_m10_ref_mods.py`): morale system as a new updater on CP phases; message listener; new GameObject type + SendCommand handler; new `.fox2` class loaded from a mod DataSet; CP phase rate override changes the `m9_phase` trace by exactly the predicted amount; hook that cancels a route switch; chained handler; AI node insert; Lua library.
  - G4 Rejections (`test_m10_rejects.py`): StrCode32 id collision with vanilla or another mod; API version mismatch; missing dependency; load-order cycle; sandbox escapes (`os` / `io` / `debug` / `require` / binary chunks); nondeterminism (unseeded random, wall clock) caught by a double run.
  - G5 Load order: two mods overriding one parameter resolve in documented order, same result on every run (`test_m10_load_order.py`).
  - G6 Overhead: registry dispatch costs at most 5 % frame time on the M3 and M9 scenarios against the pre-registry baseline (`test_m10_perf.py`).
  - G7 `natives_owner.json` covers 100 % of the bindings in `m4_lua_bindings.json` (`test_natives_owned.py`).
  - Common gate C1-C8.

## M11 Asset formats [PLANNED] — textures, models, rigs, fova, parts, language, sound containers
- `.ftex/.ftexs`, `.fmdl`, `.frig/.frdv`, `.fv2`/fova, `.parts`, `.lng`; `.sdf/.sbp` and Wwise `.bnk` / `.wem` as containers (no audio decode: M21); texture path recovery (E2). Readers and writers; formats registered through the M10 loader registry.
- **Gate:**
  - G1 Census: every file of each type listed with counts and versions from `FileInventory.json` (`test_m11_census.py`).
  - G2 Round trip: byte-identical rewrite of every file of every format (`test_m11_formats_all.py`, slow).
  - G3 Coverage: zero undecoded bytes outside payloads, or each gap listed [?] in the spec; the codec's unknown-range report equals the spec's list (`test_m11_formats_all.py`).
  - G4 Textures: every `.ftex/.ftexs` decodes to RGBA; pixel-identical to an independent decoder on a stratified sample of at least 2,000 textures covering every pixel format (`test_m11_textures.py`).
  - G5 Models: every `.fmdl` decodes; every vertex format parses; bounds recomputed from vertices equal stored bounds within float32 epsilon on every file (`test_m11_models.py`).
  - G6 Rigs: every `.frig/.frdv` hierarchy valid (parents exist, no cycles), 100 %; bone-name resolution reported (`test_m11_rigs.py`).
  - G7 Outfits: every fova / parts combination in vanilla data resolves its referenced files in the QAR inventory, 100 % (`test_m11_fova.py`).
  - G8 Language: every `.lng` entry decodes; every lang id used in vanilla Lua resolves in every language file; 20 ids equal the live game's own lookup (`test_m11_lang.py`).
  - G9 E2: every texture referenced by an `.fmdl` resolves to a QAR entry, 100 %; newly named textures reported (`test_m11_textures.py`).
  - G10 Sound containers: every `.sdf/.sbp` lists, extracts and rebuilds byte-identical; every `.bnk` section tree parses with object counts reported (`test_m11_sound_containers.py`).
  - G11 Live load list: the assets the engine says f30010 loads equal the live resource request trace (FoxTrace) (`test_m11_load_list.py`).
  - Common gate C1-C8.

## M12 Sound & UI logic [PLANNED] — sound events, music states, menus, iDroid, HUD (headless)
- Sound event layer (`TppSoundDaemon`, posted events, emitters, switches / states / RTPCs driven by gameplay, bank load with blocks); UI logic (title, pause, iDroid tabs, mission prepare, HUD state, popups beyond M4 / M5, loading tips). No playback (M21), no drawing (M20).
- **Gate:**
  - G1 Sound events: for 3 recorded scenarios (boot → title, free-roam sneak, base alert), the posted events (event id, emitter, frame) equal live, order exact, frame ±1 (`test_m12_sound_events.py`).
  - G2 Music: phase-music switch / state changes equal live on the `m9_phase1` / `m9_phase2` runs (`test_m12_music.py`).
  - G3 Banks: bank load / unload follows block loads exactly as live on both maps (`test_m12_banks.py`).
  - G4 Menus: title, pause, iDroid (map, missions, Mother Base tabs), mission prepare: state sequence for a scripted input replay equals live, at least 5 menus, every captured transition covered (`test_m12_ui.py`).
  - G5 HUD: HUD state flags (phase indicator, reflex, weapon / item selector, markers) equal live per frame over a 60 s run (`test_m12_hud.py`).
  - G6 Residue: M4 / M6 open raisers (`TitleMenuReady`, `RequestPlayRecordClearInfo`) decoded or recorded as [?] with evidence (`test_m12_ui.py`).
  - Common gate C1-C8.

## M13 Open world complete [PLANNED] — both maps, every block level, clock, weather, random numbers (headless)
- Afghanistan and Africa fully streamed (large / small / LOD blocks), mission areas (hot / outer zones), location changes (heli travel), clock and time skips, weather state machines; the game's random number generator.
- **Gate:**
  - G1 Random numbers: the game's generator reproduced bit-exact for 10^6 draws against `re_emulate` on the exe function, and seeded state equals live at mission start (`test_m13_rng.py`).
  - G2 All blocks: every block of both maps loads in the engine without error, 100 % of the FSTB lists (`test_m13_blocks_all.py`, slow).
  - G3 Traversals: 4 recorded traversals (2 per map, at least 10 min each, walk, drive and warp): block load / unload message order equals live; frame within the run-to-run tolerance (`test_m13_traversal.py`).
  - G4 Clock: engine clock equals live `vars.clock` at every sample over 30 min of game time, time skips included (`test_m13_clock.py`).
  - G5 Weather: transitions equal live for forced runs (exact) and free runs (equal given the G1 seed) (`test_m13_weather.py`).
  - G6 Zones: hot / outer zone enter and leave messages equal live on the traversal runs (`test_m13_traversal.py`).
  - G7 Location change: heli travel f30010 → f30020 runs through the game's own flow; chunk and block order equal live (`test_m13_location_change.py`).
  - G8 Mod: a mod-added small block with entities streams in at the right window (`test_m13_mod_block.py`).
  - Common gate C1-C8.

## M14 Collision & physics [PLANNED] — shape trees, queries, character controller, rigid bodies
- Typed `.geom` shape trees (E30), `.ph` / `.sim` `PhObjectDesc`; raycast, shape cast, overlap; character controller for Player2 and Soldier2 (slopes, steps, ledges, stance capsules) fed with recorded root motion until M16; rigid bodies (props, barrels). Hot paths in C++ behind `pybind11`.
- **Gate:**
  - G1 Shapes: every `.geom/.geoms` shape tree typed with zero undecoded bytes; shape counts equal the exe reader under `re_emulate` on a 200-file sample (`test_m14_shapes.py`).
  - G2 Raycasts: at least 5,000 of the game's own captured queries (sight, bullets, ground probes): hit / miss equal 100 %, hit point within 1 cm, normal within 1°, material equal (`test_m14_raycast.py`).
  - G3 Consistency: downward raycasts on terrain equal M7 height queries within 5 mm (`test_m14_raycast.py`).
  - G4 Character controller: recorded input runs (walk, run, crouch, prone, slopes, stairs, ledges, 20 min total) with recorded root motion: position within 2 cm per step, under 10 cm drift per 60 s window, grounded / falling sequence equal (`test_m14_controller.py`).
  - G5 Soldiers: realized soldier positions on the M9 route runs within 5 cm (`test_m14_controller.py`).
  - G6 Rigid bodies: at least 50 recorded prop events (kick, shot, explosion): rest position within 10 cm, rest time within 0.2 s (`test_m14_rigid.py`).
  - G7 Speed: `cpp == py` on G2 and G4; the M17 scenario's physics step under 2 ms per frame on the reference PC (`test_m14_perf.py`).
  - G8 Mod: a new collision shape and physics material from a mod (`test_m14_mod.py`).
  - Common gate C1-C8.

## M15 Combat & equipment [PLANNED] — weapons, ballistics, hits, damage, CQC logic, items, Fulton (headless)
- Equip / weapon tables, ammo, firing, projectiles, hit detection on M14, damage model (body parts, lethal / non-lethal, armour), explosives, CQC state logic, items (decoy, supply drop), Fulton, inventory and loadouts; soldier reactions through M9.
- **Gate:**
  - G1 Parameters: every equip table decodes; values equal live `TppEquip` queries for every exposed equip id (`test_m15_equip.py`).
  - G2 Ballistics: at least 1,000 recorded shots: impact point within 2 cm up to 100 m, time to impact within 1 frame (`test_m15_ballistics.py`).
  - G3 Hits: body part and damage equal live on at least 500 hits (lethal, non-lethal, armoured) (`test_m15_damage.py`).
  - G4 Explosives: who is hit and the damage equal live on at least 50 explosions (`test_m15_damage.py`).
  - G5 Fulton: success / failure equals live given the M13 generator state on at least 100 extractions (`test_m15_fulton.py`).
  - G6 CQC: grab, choke, throw, interrogate state sequences equal live (timings from recordings until M16) (`test_m15_cqc.py`).
  - G7 Reactions: soldier state sequences in combat runs equal live (M9 capture protocol, free runs) (`test_m15_reactions.py`).
  - G8 Mod: a new weapon (parameters + projectile) and a new item through the API (`test_m15_mod.py`).
  - Common gate C1-C8.

## M16 Animation [PLANNED] — clips, motion graphs, motion events, root motion, ragdoll
- `.mtar/.gani` clips, `.mog` motion graphs (least understood Fox format: new knowledge), motion events, layers / blends, foot IK, root motion (replaces M14 / M15 recordings), ragdoll blend with M14.
- **Gate:**
  - G1 Formats: every `.mtar/.gani/.mog` decodes and round-trips byte-identical; gaps listed [?] (`test_m16_formats_all.py`, slow).
  - G2 Poses: at least 30 reference clips (locomotion, CQC, soldier, buddy): local bone transforms equal live captures within 0.5 mm / 0.1° every frame (`test_m16_poses.py`).
  - G3 Motion graph: state / transition sequence equals live for player and soldier runs, every transition (`test_m16_graph.py`).
  - G4 Root motion: M14 G4 tolerances still met with engine root motion instead of recordings (`test_m14_controller.py` in live-root mode).
  - G5 Motion events: footstep / sound / effect events equal live and feed M12 G1 (`test_m16_events.py`).
  - G6 Ragdoll: at least 30 recorded knockdowns: final bone positions within 5 cm (`test_m16_ragdoll.py`).
  - G7 Mod: a new clip and a new motion-graph state through the API (`test_m16_mod.py`).
  - Common gate C1-C8.

## M17 Headless slice [PLANNED] — one free-roam area, player + one AI type, input replay, zero recorded natives
- One Afghanistan base, Player2 + Soldier2, every system from M3-M16 together; input recorder (live KB+M) and replay into the engine.
- **Gate:**
  - G1 Replays: 5 recorded 60 s runs (sneak, alert, combat, CQC, Fulton): full state trace (player, soldiers, CP phase, damage, blocks, sound events, UI) equals live within each system's tolerance (`test_m17_slice.py`).
  - G2 Drift: one 10 min replay stays within tolerance (`test_m17_slice.py`).
  - G3 No recordings: the native replay fixture is not loaded (asserted); every native called has an implementation (`test_m17_slice.py`).
  - G4 Determinism: two engine runs byte-identical (`test_m17_slice.py`).
  - G5 Mods together: all reference mods from M10-M16 loaded at once; null mod changes nothing; the morale mod changes only the predicted values (`test_m17_mods.py`).
  - G6 Speed: simulation at least real time (60 frames per second) on the reference PC (`test_m17_perf.py`).
  - Common gate C1-C8.

## M18 Full cast [PLANNED] — every soldier type, animals, buddies, heli, vehicles, bosses
- Every Soldier2 variant, animals, buddies (D-Horse, D-Dog, Quiet, D-Walker), support heli, vehicles (light vehicle, truck, APC, tank, walker gear), bosses (TppSahelan2: `SAHELAN.md`; others), each a content pack on the Mod API.
- **Gate:**
  - G1 Behaviour: per family, state sequences from at least 2 live runs reproduced (`test_m18_family_<name>.py`, one per family).
  - G2 Vehicles: driving replays: position within 10 cm over 30 s, state sequence exact (`test_m18_vehicles.py`).
  - G3 Buddies: command responses (mark, cover, call, ride) equal live (`test_m18_buddies.py`).
  - G4 Bosses: fight phase sequences equal live, at least 2 recorded fights per boss (`test_m18_bosses.py`).
  - G5 Packs: every family loads and unloads as a pack; with all packs removed, M17 still passes (`test_m18_packs.py`).
  - G6 Mod: a new buddy and a new vehicle built only through the public API, no engine change, pass their fixtures (`test_m18_mod.py`).
  - Common gate C1-C8.

## M19 Missions & progression [PLANNED] — missions, objectives, demos, Mother Base, saves
- Main and side missions, objectives, checkpoints, results and ranking, demos (cutscene logic and timing), offline Mother Base (staff, development, GMP, base building), save read / write.
- **Gate:**
  - G1 Saves: every save field decoded; load + resave byte-identical for 10 recorded saves; an original save loads and continues (`test_m19_saves.py`).
  - G2 Main missions: recorded playthrough replays of every main mission end with svars and save image equal live (`test_m19_missions.py`; milestone checkpoint at 5 missions).
  - G3 Side ops: at least 20 side ops, same check (`test_m19_missions.py`).
  - G4 Demos: event timelines equal live, order exact, timing ±1 frame (`test_m19_demos.py`).
  - G5 Mother Base: staff / development / GMP state after a scripted action sequence equals the live save (`test_m19_mb.py`).
  - G6 Results: mission score and rank equal live (`test_m19_missions.py`).
  - G7 Mod: a new mission pack (own Lua, locators, routes) runs through the API (`test_m19_mod.py`).
  - Common gate C1-C8.

## M20 Rendering [PLANNED] — reference renderer, renderer last
- Materials / shaders (specified from captures, no copied shader code), terrain, models, lighting, shadows, post, effects (E8), UI drawing, camera; viewer (D3D11 or Vulkan, ImGui via vcpkg). Enhanced rendering is MOD-E, a separate mode.
- **Gate:**
  - G1 Capture: RenderDoc capture of the live game works with plugins removed; procedure written (risk item, may be done any time) (`test_m20_capture.py` checks the stored capture set).
  - G2 Passes: at least 20 reference frames (day, night, both maps, interior, weather, UI): per-pass mean absolute error at most 2/255, 99th percentile at most 8/255 (`test_m20_frames.py`).
  - G3 Draw set: meshes and LODs drawn per frame equal live, 100 % (`test_m20_frames.py`).
  - G4 Camera: matrices equal live within float32 epsilon on replay runs (`test_m20_camera.py`).
  - G5 Speed: reference scenes at 60 fps, 1080p, on the reference PC (`test_m20_perf.py`).
  - Common gate C1-C8.

## M21 Audio output [PLANNED] — Wwise-compatible playback
- `.wem` decoding, bank hierarchy behaviour (containers, random / sequence, switches, states, RTPC curves), 3D attenuation, busses and mixing; written from specs, no Wwise SDK code.
- **Gate:**
  - G1 Decode: every `.wem` decodes; PCM equals an independent decoder within codec tolerance (`test_m21_wem.py`, slow).
  - G2 Voices: for the M12 G1 runs, voices started per event (sound ids, container choices given the M13 generator) equal live (`test_m21_voices.py`).
  - G3 Levels: emitter level by distance and RTPC equals live within 1 dB on test scenes (`test_m21_levels.py`).
  - G4 Output: loopback recordings of live and engine audio correlate at least 0.9 per 1 s spectrogram window on the M17 replays (`test_m21_output.py`).
  - Common gate C1-C8.

## M22 Playable game [PLANNED] — rendering + audio + input on the verified headless game
- **Gate:**
  - G1 Slice: M17 replays rendered with audio: M17 G1 traces hold and sampled frames meet the M20 tolerances (`test_m22_slice.py`).
  - G2 Mission: a full main-mission replay on the rendered engine ends equal to live (M19 G2) (`test_m22_mission.py`).
  - G3 Input: KB+M and pad bindings equal the game's key configuration table; input to simulation latency at most 1 frame (`test_m22_input.py`).
  - G4 Speed: 60 fps on the reference PC across the slice (`test_m22_perf.py`).
  - Common gate C1-C8.

## M23 Standalone runtime [PLANNED] — C++ frame loop, packaging
- No Python in the frame loop (Python stays the reference and the tools); installer that finds the player's own game copy; no game bytes shipped.
- **Gate:**
  - G1 Equivalence: C++ runtime equals the Python reference on every fixture of the suite (`test_m23_equivalence.py`).
  - G2 Mission: a full mission at 60 fps, 1080p, no replay data (`test_m23_perf.py`).
  - G3 Package: clean VM + player's game copy runs; the package contains zero game-derived bytes (scan against the QAR hash inventory) (`test_m23_package.py`).
  - G4 Soak: 24 h run, no crash, memory growth under 1 % per hour (`test_m23_soak.py`).
  - Common gate C1-C8.

## M24 Mod platform 1.0 [PLANNED] — API freeze, asset packs, native plugins, mod manager
- Semantic versioning and deprecation policy, asset packs (M11 writers + MOD-C importers), native plugins through a C ABI, mod manager (load order, conflict report), docs and examples on the Pages site, enhanced-mode switch.
- **Gate:**
  - G1 Surface: every public API symbol documented, versioned and tested; API dump equals the docs (`test_m24_api_surface.py`).
  - G2 Compatibility: every 0.x reference mod runs on 1.0 or is refused with a precise error; 1.0 mods run on later 1.x builds (`test_m24_compat.py`).
  - G3 ABI: a C plugin built with MSVC and one built with clang both load and pass (`test_m24_abi.py`).
  - G4 Isolation: a failing Lua mod is unloaded without stopping the game; a native plugin crash is reported with the mod named (`test_m24_isolation.py`).
  - G5 Examples: one example mod per area (buddy, vehicle, soldier, world, nav world, AI behaviour, weapon, mission, renderer feature) built from the docs alone passes its fixtures (`test_m24_examples.py`).
  - G6 Vanilla: full suite identical with no mods and with every example mod disabled (`test_m24_examples.py`).
  - Common gate C1-C8.

## Mod track [parallel] — tools and authoring for modders
Each item starts when its dependencies pass. **MOD-A is out of scope for now (Luc, 2026-11-04):** its output is deployed to and tested in the real game, which the 2026-10-28 rule (engine and RE only, no mod deploys or playtests) excludes. The in-engine Mod API (M10, M24) is engine work and in scope.

| Item | Builds on | Delivers | Gate |
|---|---|---|---|
| MOD-A Toolkit for the original game [OUT OF SCOPE for now] | M1, M7, M8 (passed) | Validated writers, route editor (`.frt`), navmesh baker (geometry → `.nav2`), headless mod-Lua harness on the M4 / M5 host | G1 every edited file round-trips and loads in the engine's own loader; G2 baker: navmeshes baked from vanilla geometry answer at least 1,000 path queries within 0.1 m of the vanilla `.nav2` (M8 oracle, offline); G3 harness reports the same Lua errors as the live game for 10 seeded broken modules; G4 (live, needs scope) baked navmesh and edited route load in the game and soldiers follow them |
| MOD-B AI sandbox | M9, M10 | Behaviour and route changes predicted by the engine before testing in game | G1 an override (phase rate, route switch) produces the predicted trace; G2 (live, needs scope) the same change in game matches |
| MOD-C Content importers | M11, M16, M24 | glTF → `.fmdl` / rig, PNG → `.ftex`, glTF animation → `.gani` | G1 imports decode with the M11 / M16 readers; G2 vanilla export → import keeps mesh, rig and clip data equal; G3 after M20, imported models render |
| MOD-D World authoring | M8, M13, M14 | New terrain, nav worlds, stage-block grids, locators, routes | G1 a new 1 km² world streams, has collision and paths (M8 oracle on its baked navmesh), and hosts a soldier passing the M9 behaviour checks; G2 editing and reverting a vanilla block gives byte-identical files |
| MOD-E Enhanced renderer | M20 | Modern lighting, higher resolutions, effects, as a separate mode | G1 M20 gate unchanged in compat mode; G2 each enhanced feature has a frame-time budget and a 1 h stability run (no NaN pixels, no device loss) |

## Out of scope
- Online play and FOBs (Konami's servers and protocol).
- Anything touching Denuvo or modifying `mgsvtpp.exe` (hard rule).

## Retired
- **Mod checkpoint and Option B mod (Sahelanthropus pilot)**, dropped 2026-10-28 (Luc): no mod work, deliverables or playtests. History in [`docs\LOG.md`](log.md); the verified RE (`docs\SAHELAN.md`, `docs\PROBES.md`, `docs\BATTLEFIELD.md`) is evidence for M8, M9 and M12.

---
<small>Source: `docs/ROADMAP.md` in the project repository &middot; generated 2026-11-04.</small>
