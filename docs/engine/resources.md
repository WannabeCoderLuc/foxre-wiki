# Resources and mission load

Clean-room spec for `Engine\resources\` and the pack-scoped part of `Engine\script\vfs.py` (roadmap M5). Tags: [V] read in the exe / matched against live data this pass, [I] inferred, [?] open.
Started 2026-10-23. Static reading of `GameBackup\MGS_TPP\mgsvtpp.exe` plus the live boot capture `Engine\tests\fixtures\m4_lua_boot.json` (cold boot → title CONTINUE → f30010).

## Summary
Loading a mission is driven from Lua, executed by two native loaders, and fed by Lua again:

1. Lua (`TppMission.Load`) sets `vars.locationCode` / `vars.missionCode` and calls `Mission.LoadLocation{force=}` and `Mission.LoadMission{force=}`. These only **latch** the request [V].
2. The **location loader** loads the location's packages (list from the Lua function registered with `Mission.SetLocationPackagePathFunc`), and the stage's common package [V/I below].
3. The **mission block controller** waits until the location is loaded, asks the Lua function registered with `Mission.SetMissionPackagePathFunc` for the mission's package list and loads it into the mission block [V].
4. Every `.lua` entry of a loaded package is a **script resource** that runs as soon as its package is loaded [V static vs live].
5. The mission script (`TppSimpleMissionData.script`, always `mission_main.lua`) then goes through `OnAllocate(subScripts)` and `OnInitialize(subScripts)`, each a coroutine resumed once per frame; when `OnInitialize` returns the mission block is activated [V].

## Lua contract (natives)
| Native | VA | Behaviour |
|---|---|---|
| `Mission.SetLocationPackagePathFunc(f)` | 0x140994670 | `f` must be a function; keeps a registry reference in global 0x142C01120 (releases the previous one) [V; arguments of the obfuscated body [I]] |
| `Mission.SetMissionPackagePathFunc(f)` | 0x140A1DEE0 | same, global 0x142C1F8C0 [V] |
| `Mission.LoadLocation(opts)` | 0x140A1FB60 | `force = opts.force` (boolean); location loader (global 0x142C011A0): +0x38 = `vars.locationCode`, flag bit 3 = force (0x140993FA0); then 0x140993F60 sets bit 2 "requested" and records `vars.locationCode`/`vars.missionCode` at +0x3E/+0x40 [V] |
| `Mission.LoadMission(opts)` | 0x140A1FBD0 | `force` likewise; 0x140A1D610: global 0x142C1F8B1 = force, 0x142A6EFE0 = `vars.missionCode`; then 0x140993F60 [V] |
| `vars` block | 0x1409AA930 | returns the vars storage; `+0x10` = `locationCode`, `+0x12` = `missionCode` (both 16-bit) [V by use] |
| `TppColoringSystem.GetAdditionalColoringPackFilePaths{missionCode=}` | 0x1405CEDA0 → 0x1405CEE80 | table of up to 8 paths; every mission except 30050 gets 2: `*0x142A1D4E0` = `/Assets/tpp/pack/fova/mecha/all/mfv_scol_c11.fpk`, `*0x142A1D4C0` = `.../mfv_scol_c07.fpk` (static pointers, runtime rewrite not checked [I]); 30050 picks one entry of the table at 0x142A1D380 by the Mother Base coloring state [?] |

The package-path functions are pure Lua (`TppMissionList.GetLocationPackagePath` / `GetMissionPackagePath`, built on `TppPackList`), so the engine only has to call them: `f(code)` under `lua_pcall`; a table result is walked with `lua_next` and each string becomes a path; a single string result is one path; on a Lua error nothing is loaded (0x140A1D000) [V].

## Mission block controller [V]
Class behind vtable **0x1422A9710** (the "mission-script owner" of `ScriptHost.md`). It is created by the DataBody of **`TppSimpleMissionBlockControllerData`**: DataBody vtable 0x1422A9890 (instance 0x60 bytes = the type DB size of `TppSimpleMissionBlockControllerDataBody`), slot 6 0x140A1D260 / slot 9 0x140A1CAC0 construct the controller (0x140A1B760, 0xA8 bytes) from the Data's `name` (+0x48) and `blockSizeInByte` (+0x78), which matches the Data's type DB offsets 72 and 120 [V]. Name of the controller class itself: no RTTI; "TppSimpleMissionBlockController" [I from its Data/DataBody].

- The Data sits in each location's stage DataSet: `afgh_stage.fox2`, `cypr_stage.fox2`, `mbqf_stage.fox2`, `mtbs_mission.fox2`, `tpptest/.../empty_stage.fox2` (name `mission_block`, e.g. 20,877,192 bytes in afgh, 33,554,432 in empty) [V data]. So the mission block exists only once a location is loaded.
- Constructor looks up the `Mission` message channel and subscribes the controller to 24 categories on it (21 named: Marker, Sound, GameObject, Trap, Demo, Timer, Terminal, Weather, Player, Radio, Subtitles, Block, Throwing, Placed, MotherBaseManagement, MotherBaseStage, Network, Video, TppSystem, SupportAttack, SupplyCbox; 0xB913232E = `UI`, 0x445FE2CA = `Nt` [V StrCode32, 2026-10-24], 0xDC05D615 [?]) and creates a block group with one block [V].
- Per-frame update = slot 2 **0x140A1E380** (state of block 0 at block+0x80: 0 empty, 1 processing, 2 loaded, 3 active, 4 [?]):
  - requested mission (0x142A6EFE0) ≠ current (+0x78) or force → new target, clear "loaded" bit;
  - block empty and a target set: wait while the location loader is busy (0x140993FF0: requested location ≠ loaded location, or its block not active); then build the package list (0x140A1D000), hand it to two Quark-table services (+0x2D8, +0x2F8, [?]), make the block depend on the blocks of `EquipCommonBlockGroup`, `CommonStageBlockGroup`, `MBStageCommonBlockGroup` when they exist, and start loading (0x14006DEC0); progress code 0x142C1F8C4 = 1;
  - block loaded (2) and it is the current target: `OnInitialize` step (0x140A1C460) once per frame; result 1 → activate the block (0x14006CFB0, code 5), 2 → unload (code 7), 0 → still running;
  - target changed while loaded/active: unload (code 7) or deactivate first (0x14006D480, code 6).
- Slot 13 **0x140A1D2E0** (block-loaded callback): finds the mission data of the block (0x140A1CB10), builds the `subScripts` table (0x140A1C990), and runs `script.OnAllocate(subScripts)` in a new Lua thread (`lua_newthread` + `lua_resume`); a yield keeps the thread for the next callback; code 2 while running, 3 when done [V].
- Function names are static `fox::String`s: 0x142C1F8E0 = `"OnAllocate"` (initialised from 0x1422A3310), 0x142C1F8F0 = `"OnInitialize"` (0x1422A9598); next to them `"OnUpdate"`, `"OnReload"` [V].
- `mvars`: the mission object (vtable 0x1422A9FB8) constructor 0x140A1E890 and destructor 0x140A1ED90 both call 0x140AE0EE0 = `_G.mvars = {}` (fresh table) [V]. Lua never creates `mvars`.
- `svars` (storage 0x142C333B8) are declared once (`DeclareSVars` 0x140AE1C70 tests the global) and freed by a finalizer that `DeclareSVars` registers (0x140AE1DD0 → 0x140AE1D20; registration through obfuscated code); f30010 declares its own svars after 40010 live, so they end with the mission [I: lifetime = mission object; engine resets them with `mvars`].
- Per frame while the mission block is active: slot 16 **0x140A1CC20** → `OnChangeSVars(subScripts, name, index)` for each logged svars change, then `OnUpdate(subScripts)` [V] (svars change log: `ScriptHost.md`).

## Location loader
Global object 0x142C011A0 (class registered by 0x140993ED0 with a `Start` method 0x140994720 [?]). +0x30 = its block group, +0x38 = requested location, +0x3C = loaded location, +0x48 flags [V]. Its update (who calls it, ordering against the mission controller) is not read yet [?]; the behaviour below is fixed by the live chunk order:

- location changed: unload the mission block, then load the location packages (`GetLocationPackagePath(code)`), then the stage's **common package** [V order vs live].
- same location (40010 → 30010 in afgh): nothing reloads; only the mission block changes [V live: no second afgh_common load].
- Common package: the location package's stage DataSet holds a `StageBlockControllerData` whose `stageBlockFile` is a `.fstb`; its header names the common package (afgh: `/Assets/tpp/pack/location/afgh/pack_common/afgh_common.fpk`) [V data]. The rest of `StageBlockControllerData` (small/large/LOD block grids around the player) is world streaming, M6.

## FSTB (stage block file) — partial
`FSTB` magic, u32 @0x10 = number of common packages, u32[] @0x14 = file offsets of NUL-terminated package paths. Both extracted files (afgh, mbqf) have one entry [V]. The remaining tables (block grids, LOD and large-block package lists, the path strings for `stagelow` LOD packs) are not decoded [?] (`fox-format` when M6 needs them).

## Packages and script resources
- A package path `X.fpk` means both `X.fpk` and `X.fpkd` (the `.fpkd` holds the DataSets and scripts) [V data].
- **Pack-scoped VFS**: files inside a package are reachable only while it is loaded; the most recent load wins for duplicate paths (`mission_main.lua` is in several mission packages) [I: shadowing rule; duplicates are byte-identical in the cases seen].
- **Script resources**: every `.lua` entry of a loaded package runs once per load (no load-once, `mission_main.lua` runs 3 times in the boot), with library semantics (a returned table is stored as the global named after the file, 0x14018BE10) [V live order; storage: ScriptHost.md].
- **Resident resources are shared**: a script that a still-loaded package already holds does not run again when another package with the same path loads; it runs anew once every holder has unloaded [V live: with IH's patched `f30010.fpkd` (adds `reinforce_block.lua`) loaded, the quest pack `quest_q52015.fpkd`, which also holds it, runs only `quest_q52015.lua` (capture `trace_m5_luaret`)]. Engine: `MissionLoader.new_scripts` / `release`.
- **Packages without a known name**: the extraction names 83 % of the QAR entries; `quest_q52015.fpk`, the `anml_*` animal packs and `decoy_svs.fpk` are found the way the engine finds every file, by PathCode64 in the archives' section tables (`Engine\script\vfs.py` `QarIndex`, pristine GameBackup archives, read-only).
- **Order**: packages in list order; inside a package the scripts run in the **reverse of their stored entry order**, which in every game package seen equals ascending path order: `init.fpkd` stores `mission_main, init_sequence` → live runs `init_sequence, mission_main`; `afgh_script.fpkd` stores `travelPlans … afgh, afgh_luxury_block_list` → live runs the reverse; `f30010.fpkd` stores `mission_main, sound, sequence, radio, orderBoxList, enemy, demo` → live runs the reverse [V static vs live]. Which of the two rules the engine implements is not distinguishable from the data [?].
- `TppSimpleMissionData` (in the mission's own package, e.g. `init_sequence.fox2`): `script` (FilePtr) = `mission_main.lua`; `subScripts` (StringMap of FilePtr) = `sequence`, `enemy`, `demo`, `radio`, `sound`, `photo` … → the `subScripts` table handed to `OnAllocate` / `OnInitialize` maps each key to that script's returned table [I: table content; the keys are the data's].

## Boot sequence (live chunks 112–169)
| Live chunks | Trigger | Packages (Lua resources) |
|---|---|---|
| 112–113 | `start.lua` → `TppVarInit.StartInitMission()` → `TppMission.Load(1, force)` | location INIT: `tpptest/.../empty.fpk`; mission 1: `gz_pause_key_setting_data.fpk`, `init.fpk` (init_sequence, mission_main) |
| 114–122 | emblem setup 6 frames after the init package (114); iDroid reload after init_sequence's two `ChangeLanguage` calls (115–118, 119–122) [V] | `emblem_list.lua` (script resource of 0x1405CF950); `mb_dvc_top.fpk` ×2 (4 UI tables each) |
| 123–125 | pre-title UI (0x14085C8C0, state 4) calls `TppVarInit.StartTitle` [V]; save past the hospital → heli space 40010 in afgh | location afgh: `afgh.fpk` (no scripts) + common `afgh_common.fpk` (fx_mtr def/rain/underwater) |
| 126–144 | same | mission 40010: `heli_common_script`, `title_sequence`, `heli_ui`, `mis_com_helicopter`, `afgh_script` (14 location scripts), `h40010_area` (photo, radio, mission_main), 2 coloring packs |
| 145–166 | title CONTINUE → `TppMission.Load(30010, 40010)` | mission 30010: `afgh_script`, `mis_com_helicopter`, `mis_com_afgh`, decoy, `mis_com_order_box` (order_box_block), `f30010.fpk` (demo … sound, mission_main), 2 coloring packs |
| 167–169 | f30010 mission-prepare sequence → script blocks | quest_block ← `quest_q52015.fpk` (`quest_q52015.lua`, `reinforce_block.lua`); animal_block ← `anml_powerPlant_SE_00.fpk` (`animal_block.lua`). Live order reinforce, quest, animal because IH's patched `f30010.fpkd` carries `reinforce_block.lua` (below) |

**Engine host result (`Engine\tests\test_m5_mission_load.py`), M5 gate PASS (2026-10-24):** with the title flow's native requests made at the boundary (two `TppUiCommand.ChangeLanguage()`, then the two mission loads), the recorded natives (M4 replay) and the save behind `TppScriptVars.LoadVarsFromSlot`, the host loads **all 58 chunks = live 112–169**, incl. the emblem table and both iDroid reloads, the three script-block chunks in vanilla order (`quest_q52015.lua`, `reinforce_block.lua`, `animal_block.lua`); the block events, the script-block slots (reinforce 0, orderBox 1, animal 2, quest 3) and the three `ScriptBlock.Load` calls match live. One known Lua error remains: heli space 40010's `DataIdentifier` locator lookup (world data, M6). Boundary: the init mission's title flow (init_sequence starts on a `Timer.Finish` message; the host has no timers / message delivery yet, M4 gate) is replaced by its native requests ("UI parameter tables" below).

**Why the live tail differs (IH):** the live game's `master\0\00.dat` (SnakeBite) holds a patched `f30010.fpkd` with `reinforce_block.lua` added as an entry; the pristine one (GameBackup `chunk2.dat`) does not [V both archives]. Live runs it with the mission package (chunk 167) and, because it is resident, not again from the quest pack. The capture fixture `m4_lua_boot.json` filters IH's own chunks by name only, so this one stayed in.

### What drives the three loads (f30010, CONTINUE) [V live: IH Lua trace `Memory\research\m5_sbtrace_20261023`]
1. `TppMain.OnAllocate` → `DeclareSVars` → (not title, not mission start) `TppVarInit.InitializeForContinue` → `TppSave.VarRestoreOnContinueFromCheckPoint` → `TppScriptVars.LoadVarsFromSlot(CHECK_POINT, GROUP_BIT_ALL, CATEGORY_MISSION)`: the saved `svars.sbl_scriptBlockName/Pack/isActive` come back (quest_block = `quest_q52015`).
2. `TppMain.OnInitialize` → `TppAnimalBlock.InitializeBlockStatus` clears animal_block's saved entry; its end calls `SetUpdateFunction` (the per-frame Lua list: `TppMission.Update`, `TppSequence.Update` …).
3. `TppSequence.Init` writes `svars.seq_sequence = Seq_Mission_Prepare`; that svar is `sync` (hence `notify`), the write is logged and the mission controller delivers `OnChangeSVars` the next frame → the sequence enters → `OnEnter` → `TppMain.OnEnterMissionPrepare` → `TppScriptBlock.ReloadScriptBlock` → **`ScriptBlock.Load(3, {quest_q52015.fpk})`** (live f4523; chunk one frame later).
4. `Seq_Mission_Prepare.OnUpdate` waits for `TppMission.CanStart()` and texture streaming (`Mission.GetTextureLoadedRate() > 0.35`, or its own 30 s timeout), then `TppMain.OnMissionCanStart` → `afgh.OnMissionCanStart` → `afgh_animal.OnMissionCanStart` → `TppAnimalBlock.UpdateLoadAnimalBlock(x, y)` with the current stage small block (live (128, 125)) → **`TppScriptBlock.Load("animal_block", "powerPlant_SE")`** (live f4677, 154 frames after 3). `TppQuest.InitializeQuestLoad` runs too; the quest block is already loading.
5. The quest's `OnAllocate` (`TppEnemy.OnAllocateQuestFova` → `LoadQuestHeli`) → **`ScriptBlock.Load(0, "/Assets/tpp/pack/soldier/reinforce/reinforce_heli_afgh.fpk")`** (no script in that pack).
6. Transitions seen live (Block message `OnScriptBlockStateTransition`): quest LOADED f4608, reinforce LOADED f4621, animal LOADED f4695 → ACTIVATED f4698 (the animal load passes `activate = true`).

The host reproduces 1–5. Inputs at the boundary: the stage small-block index is the recorded native answer (world streaming is M6); the save values are the minimal set the gate reads, taken from the live dump (`Engine\tests\fixtures\m5_save_image.json`: gvars `sav_varRestoreForContinue`, `qst_currentQuestName`, `qst_questActiveFlag` + svars `sbl_*`, each tagged; found by ablation; the full 271-gvar dump stays in `Memory\research\m5_sbtrace_20261023`); with no texture streaming the prepare step takes its 30 s timeout (host clock 60 frames/s), which keeps step 3 before step 4 as live.

## Script blocks [V]
Engine: `Engine\resources\blocks.py` (`ScriptBlocks`), test `Engine\tests\test_m5_script_blocks.py`.

- **Slots:** 8 global slots, objects at **0x142B72C30[8]**, their name StrCode32 at **0x142B72C10[8]**, live count 0x142B72C70 [V]. A slot is created by a **`ScriptBlockData`** entity (type DB: `name` +72, `dataSet`, `prerequisites` +120 String array, `sizeInBytes` +136, `enabled` +140) when its DataSet loads, and freed when it unloads: ctor **0x1401814F0** takes the first free slot, stores the name hash and the slot index (+0x9C), creates a one-block group (+0x38) and copies the prerequisite names (+0x50, 8 entries, count +0xA0); dtor 0x140181950 clears the slot [V]. In TPP the Data sits in the mission's own package: f30010 = `orderBoxBlock`, `animal_block`, `quest_block` (`f30010_sequence.fox2`) and `reinforce_block` (`afgh_common_reinforce.fox2`) [V data]. Slot order follows creation order [I: DataSet load order inside the package].
- **Object** (vtable 0x1420EA438, interface 0x1420EA470 at +0x30): +0x40 requested package list (`fox::Path` array), +0x90 script table (registry ref), +0x98 running coroutine ref, +0x9C slot, +0xA8 flags: 0x01 request, 0x02 pending (unload, then load), 0x04 reload, 0x08 activate wanted, 0x20 initialized, 0x40 terminate; +0xA9 frame countdown before a load (set to 3 by vtable slot 4 0x1401838C0 [?] trigger) [V].
- **Natives** (`ScriptBlock.*`, all [V]):

| Native | VA | Behaviour |
|---|---|---|
| `GetScriptBlockId(name or hash)` | 0x1401839F0 | number = StrCode32, string = hashed; first slot with that hash, else `SCRIPT_BLOCK_ID_INVALID` (4294967295) |
| `GetCurrentScriptBlockId()` | 0x1401839C0 | global 0x1429E4BF0 = slot whose script is being called, else INVALID |
| `Load(id, nil / path / {paths})` | 0x140183B50 → 0x140183200 | builds the list (string paths; numbers = path ids; empty = none); a string becomes a path through 0x140085670 → 0x1400858D0 → path code 0x14003DB30 and is appended only when the code is non-zero: `""` fails the normaliser 0x14003DF90 (length 0 → false) → code 0 → nothing appended, so **`Load(id, "")` = `Load(id, nil)` = empty list = unload** [V static, both resolver branches 0x14003DB60 / 0x14003DD20 end in `xor eax, eax`]; a list different from +0x40 replaces it and sets flags `(f & ~0x08) \| 0x01` (request, activate cleared) |
| `Activate(id)` / `Deactivate(id)` | 0x140183910 → 0x140181E30 / 0x140183960 → 0x140182700 | set / clear 0x08; acts at once when the block is loaded+initialized / active |
| `Reload(id)` | 0x140184020 → 0x1401837B0 | ignored while a request is pending; processing → flag 0x04; loaded → reload now |
| `GetScriptBlockState(id)` | 0x140183A80 → 0x140182A90 | request pending → PROCESSING (1); block empty → EMPTY (0); loaded → INACTIVE (2) once initialized, else PROCESSING; active → ACTIVE (3) |
| `IsProcessing(id)` | 0x140183AF0 → 0x140183120 | request pending, or block neither empty nor active, or loaded but not initialized |
| `UpdateScriptsInScriptBlocks()` | 0x140184070 → 0x140184650 | `script.OnUpdate()` (pcall) for each slot whose block is loaded/active, initialized, no request |
| `ExecuteInScriptBlocks(f)` | 0x1401839B0 → 0x140182840 | `f(slot, script or nil)` for each existing slot |

- **Per-frame update** (vtable slot 2 **0x140184340**): (1) request: clear reload; when the block is not processing and not loaded-but-uninitialized, flags → pending (request, reload, 0x10 and initialized cleared). (2) pending: a non-empty block is deactivated (if active), `OnTerminate` runs (0x140184260), the block unloads; an empty block waits out the countdown, clears pending and the script, then starts loading the list with the prerequisite blocks as dependencies (0x14006F8C0, 0x14006DEC0). (3) loaded and not initialized: one `OnInitialize` resume (0x140182D40, coroutine on a new Lua thread, no arguments, current id set; finished or failed → initialized); loaded + initialized: reload (0x04) or activate (0x08, 0x14006CFB0); active: reload, or deactivate (0x14006D480) when 0x08 is clear. (4) terminate flag: unload [V].
- **Block-loaded callback** (interface slot 7 **0x140182B20**, once per frame while the block is processing): first call finds the script = the first resource of the block's packages that is a Lua script resource with a table (0x140184080, type at 0x142B72C90) and resumes `script.OnAllocate()` on a new thread; returns 2 while it yields, 0 when done, 3 on error [V].
- **Transitions:** interface slots 1/6/3/5 post message `OnScriptBlockStateTransition` (StrCode32 0x3EE65CAF, category 9 = `Block`: Lua receives `Block.OnScriptBlockStateTransition(blockName, state)` [V live IH log 2026-10-24]) with (name hash, `TRANSITION_LOADED` 0 / `DEACTIVATED` 2 / `EMPTIED` 3 / `ACTIVATED` 1) [V]; the engine logs them as `script_block_transition` events (no message bus in the host yet).
- Strings: 0x1420E9C18 `OnAllocate`, 0x1420E9C28 `OnInitialize`, 0x1420E9C38 `OnTerminate`, 0x1420E9C48 `OnUpdate` [V].
- Lua side: `TppScriptBlock` keeps pack lists per block name (`RegisterCommonBlockPackList`), saves name/pack hashes in `svars.sbl_*` and reloads them in `TppMain.OnEnterMissionPrepare` → `ReloadScriptBlock`; `TppReinforceBlock` calls `ScriptBlock.Load` directly with a reinforce package; `TppQuest` / `TppAnimalBlock` go through `TppScriptBlock.Load` [V Lua]. What triggers them in the boot: "What drives the three loads" above.

### Soldier common-motion block [V]
`TppSoldier2CommonBlockController` (global 0x142C1D9E0, object at +0x10): `SetPackagePathWithPrerequisites{path=, prerequisites={≤8}}` (0x1409FA460) replaces the path (+0x70; a new path clears ready bits 0x02/0x04 of +0x91) and the prerequisite list; the update (0x1409FA7A0) loads an empty block (with prerequisites), activates a loaded one whose path matches, unloads a stale one; ready bit 0x04 = (no path and block empty) or (path loaded and block active). `IsReady` (0x1409FA3D0) returns that bit. `TppEnemy.LoadSoldier2CommonBlock` waits on it inside `TppMain.OnAllocate` [V]. Engine: `CommonMotionBlock`, one update after the request [I timing].


## UI parameter tables: iDroid (MbDvc) package loads [V]
Engine: `Engine\resources\ui.py` (`IDroid`); tests `test_m4_script_host.py` (boot load), `test_m5_mission_load.py` (`test_ui_tables`, full chunk order). Live captures `Memory\research\trace_m5_mbdvc_20261023_164520` (hooks 0x14092B310, 0x140969A60, 0x1405D0BF0, `luaL_loadbuffer`) and `trace_m5_lang_20261024_135254` (adds `ChangeLanguage` / `IsChangeLanguage` / `SetPlatformLanguage` return hooks, the reload state machine 0x14092ED80, its language step 0x14090FA70, the emblem setup 0x1405CF950), 2 runs each.

- **What they are:** the four `mbdvc_*` tables are **not** loose script loads, they are the `.lua` entries of the package `/Assets/tpp/pack/mbdvc/mb_dvc_top.fpk` (00.dat / chunk0), run in reverse entry order like every package (location, mbstage, mission, pause_help) [V live]. The package is loaded 3 times per boot, always from caller 0x1408626B2; ~5 frames after each load the table object (vtable 0x14227F940, slot 0 0x140969A60) requests the 3 map tables as script resources again (no new chunk loads) [V live].
- Loader chain [V static]: `MbdvcBootBody` (DataBody of `MbdvcBootData`; class descriptor 0x142BF17C0, size 0x90, module TppUi; vtable 0x142243C90, slot 6 / slot 14 → 0x140862640) creates the block groups `MbDvcMainBlockGroup` / `MbDvcChildBlockGroup` (0x14092AE10) and loads `mb_dvc_top.fpk` by PathCode64 0x5229CB6C81444814 (0x14092B310). `MbdvcBootData` is in `/Assets/tpp/pack/ui/ui_default_data2.fpk` (`uig_mb_dvc.fox2`), which the iDroid manager (global 0x142BF1518) loads from its per-frame update 0x14092DEA0 (string 0x14226FF60).
- **Trigger = every language change** [V static + live]:
  - `TppUiCommand.ChangeLanguage()` (0x1408CE490) reads the configured language (config object 0x140530200, vt+0x188); if < 11 it becomes the requested language (service vt+0x258) when it differs from vt+0x260, and the change-pending flag is set (vt+0x248(1)). The language service is QuarkSystemTable+0x98 → +0x40 → +0x50. `IsChangeLanguage()` (0x1408D24E0) returns the pending flag (vt+0x250).
  - The iDroid UI update (vtable 0x142271218 slot 2, 0x14092E7C0), while the flag is set, runs the state machine 0x14092ED80(requested): state 0 returns done at once when the current language (vt+0x268) equals the requested one; otherwise it sets the reload flags (manager +0x83A, +0x28) and advances one state per update: 1 waits for the UI to be loaded, 2–4 tear down, 9 loads the language's font/text packages (0x14090FA70, a switch over 11 languages with two path codes each), **0xE sets the manager's load flag +0x839**, which the next update acts on (0x14092DEA0 / 0x14092F080 run before the language step) → `ui_default_data2` → `MbdvcBootBody` → `mb_dvc_top`; 0xF / 0x11 wait for the loads; on done the flag is cleared (vt+0x248(0)), then vt+0x270(0).
  - Live the boot makes **three** calls and each runs the full reload with requested language 0 (2 runs): `TppUiBootInit.lua` (after `SetPlatformLanguage`, f0) → `mb_dvc_top` f25/26 (live chunks 36–40); init_sequence `Seq_Demo_SetSavedLanguage` (after `TppSave.LoadConfigDataFromSaveFile` + `LoadVarsFromSlot(CONFIG)`, f287/289) → f338/340 (chunks 115–118); `CreateOrLoadSaveData` (`if fileExists[CONFIG] then ChangeLanguage()`, f387/388) → f438/439 (chunks 119–122). State machine active f0–59, f287–366, f387–483; step 9 runs 9 / 21 frames after the call. So the current language never equals the requested one at these calls; what vt+0x268 returns is not decoded [?].
  - Boot position: the boot load runs on worker threads between `TppMath.lua` and `TppSequence.lua`, interleaved with start.lua's async libraries in a different order in each of 3 runs (fixture: location, TppLocation, mbstage, mission, pause; trace_m5_lang run 1: location, mbstage, mission, TppSave, pause, TppLocation; run 2: location, mbstage, TppSave, mission, pause, TppLocation) [V live].
- **`emblem_list.lua`:** chunk 3 (boot, before init.lua) and chunk 114. The second load is the emblem setup **0x1405CF950**: it makes `/Assets/tpp/ui/Script/emblem_list.lua` a script resource (+0x40), registers 0x1405D0BF0 as its reload callback (+0x48, via 0x140969690), then reads 4 emblem tables (0x142BDD1A0–B8) [V static]. Live it runs at f222/223, 6 frames after the init mission's scripts (f216/217), called from obfuscated code (0x145D88100); the reload callback never fired (4 runs) [V live]. The init package holds `EmblemBlender.fox2` (DataSet: `UiFontGroupData` emblem fonts, `EmblemBlender` "Blender", `TexturePackLoadConditioner`) and is the only package of the boot with an `EmblemBlender` Data [V data]; that this Data's body calls the setup is [I].
- **Engine (`IDroid`, `Engine\resources\ui.py`):** natives `ChangeLanguage` / `IsChangeLanguage` as above (configured language 0 [V live value; source I]); a reload on every call, as live; the state machine takes 16 updates to the `mb_dvc_top` load and 18 to the end = the decoded step count with every wait done at once (no IO in the host; live IO stretches it to 25 / 51 frames). `mb_dvc_top` is (re)loaded through the loader in the block `MbDvcMainBlockGroup` (unload, load: its scripts run again). Emblem: a loader package hook schedules the setup 6 frames after a package with an `EmblemBlender` entity loads. The iDroid ticks inside `ScriptHost.boot` and as a loader controller afterwards.
- **Boundary:** the host does not run the init mission's title flow: init_sequence starts from `Timer_WaitStartingGame` → `Timer.Finish` → `Seq_Mission_Prepare.MissionGameStart` (TppSequence); timers and message delivery to the mission's `OnMessage` are not in the host yet (`GkEventTimerManager.Start` 0x1404AC310, `Mission.GetCurrentMessageResendCount` 0x140A1FB30 = global 0x142C1FD44, `OnMessage` string users 0x140994D10 / 0x140AD9EA0) → M4 gate. The gate test makes the flow's two `ChangeLanguage()` calls and waits on `IsChangeLanguage()` like the Lua.

## Open [?]
- Script blocks: ~~per-frame caller~~ answered 2026-10-24 [V live `trace_oq_callers`]: the slot update is called from the per-entry wrapper 0x14017E110 (vtable 0x1420E9140 slot 11; object +0x88, state +0x20: 0 → vt+0x10 update, 1 → vt+0x18 ready → 2), every frame after the mission controller (updater prio 4), 7 objects in f30010; still open: who calls the wrapper's slot 11; the countdown trigger (slot 4 0x1401838C0, 0 calls in a normal boot [V live]); the order in which 0x140184080 walks a block's resources (engine: first table in run order); the `OnScriptBlockStateTransition` message category (9) and its delivery (no message bus in the host yet).
- svars change log (implemented only for TppSequence entering `Seq_Mission_Prepare`): the per-var flag 0x40 tested at 0x140AE0E5E is taken to be the declaration's `notify` bit; whether an unchanged write is logged (engine: changes only); the second path 0x140AE29D0, `OnSynchronizeSVars`, overflow, other `OnChangeSVars` consumers (`ScriptHost.md`).
- The location loader's update function and the exact frame order between location, common block and mission block.
- The two Quark-table services that receive the mission package list (+0x2D8, +0x2F8 of the table at QuarkSystemTable+0x98).
- FSTB beyond the common-package header.
- `Mission.RequestToReload` (0x140A1FA40) and `TppMission.RequestLoad` (reload without location change).

## Evidence
| VA | What it shows | Tag |
|---|---|---|
| 0x1408CE490 / 0x1408D24E0 | `TppUiCommand.ChangeLanguage` / `IsChangeLanguage`: requested language + change-pending flag of the language service | [V] |
| 0x14092E7C0 / 0x14092ED80 / 0x14090FA70 | iDroid UI update, language-change state machine (state 0xE → load flag +0x839), language packs | [V] |
| 0x14092B310 | `MbdvcBootBody` loads `mb_dvc_top.fpk` | [V] |
| 0x1405CF950 / 0x1405D0BF0 | emblem setup (`emblem_list.lua` script resource) / its reload callback | [V] |
| `trace_m5_lang_20261024_135254` | 2 runs: 3 `ChangeLanguage` calls → 3 reloads (requested 0), `mb_dvc_top` +25/+51 frames, emblem setup f222, boot-window interleaving | [V live] |
| 0x140A1FB60 / 0x140A1FBD0 | `Mission.LoadLocation` / `LoadMission`: read `opts.force`, latch vars codes | [V] |
| 0x140993FA0 / 0x140993F60 / 0x140993FF0 | location request latch / requested flag / "location busy" test | [V] |
| 0x140A1D610 | mission request latch (0x142C1F8B1 force, 0x142A6EFE0 code) | [V] |
| 0x140994670 / 0x140A1DEE0 | `Set{Location,Mission}PackagePathFunc`: registry refs 0x142C01120 / 0x142C1F8C0 | [V] |
| 0x140A1D000 | calls the mission Lua function with the code under `lua_pcall`, table/string result → path list | [V] |
| 0x140A1E380 | mission block controller update (vtable 0x1422A9710 slot 2), state machine above | [V] |
| 0x140A1CC20 | mission controller slot 16, every frame while the mission block is active: `OnSynchronizeSVars` on a flag, `OnChangeSVars(subScripts, name, index)` per logged svars change, then `OnUpdate(subScripts)` (string 0x142C1F970 ← 0x1422A95A8), all under `lua_pcall` | [V] |
| 0x1401814F0 / 0x140181950 | ScriptBlock ctor / dtor: 8 slots 0x142B72C30, names 0x142B72C10 | [V] |
| 0x140184340, 0x140182B20, 0x140182D40, 0x140184260 | slot update, block-loaded callback (OnAllocate), OnInitialize step, OnTerminate | [V] |
| 0x1401839F0, 0x140183B50, 0x140183910, 0x140183960, 0x140184020, 0x140183A80, 0x140183AF0, 0x140184070, 0x1401839B0 | `ScriptBlock.*` natives (table above) | [V] |
| 0x1401822D0 / 0x140182370 / 0x140182410 / 0x140182230 | `OnScriptBlockStateTransition` (0x3EE65CAF) with LOADED / EMPTIED / ACTIVATED / DEACTIVATED | [V] |
| 0x1409FA460 / 0x1409FA7A0 / 0x1409FA3D0 | soldier common-motion block: set path, update, `IsReady` | [V] |
| `trace_m5_luaret_20261023_115514` | 2 runs: ScriptBlock natives + chunk loads interleaved; slots, Load arguments | [V live] |
| `m5_sbtrace_20261023` (IH log; module `Tools\FoxTrace\ih\InfM5ScriptBlockTrace.lua`) | Lua call path of each load, Block messages, frames; svars `sbl_*` at f30010 | [V live] |
| GameBackup `chunk2.dat` vs live `0\00.dat` `f30010.fpkd` | IH adds `reinforce_block.lua` | [V] |
| 0x140A1D2E0 / 0x140A1C460 | `OnAllocate` / `OnInitialize` coroutines with `subScripts` | [V] |
| 0x140A1B760, 0x140A1D260, 0x140A1CAC0 | controller ctor (message subscriptions, block group); DataBody slots that build it | [V] |
| 0x140A1E890 / 0x140A1ED90 → 0x140AE0EE0 | mission object ctor/dtor reset `mvars = {}` | [V] |
| 0x14085C8C0 | pre-title sequence state 4 calls Lua `TppVarInit.StartTitle` (strings 0x142240FB0/0x142240FC0) | [V] |
| 0x1405CEDA0 / 0x1405CEE80 | coloring pack list | [V] |
| `fox_edb.json` | `TppSimpleMissionBlockControllerData` (name +72, blockSizeInByte +120), `...DataBody` size 96, `TppSimpleMissionData` (script, subScripts) | [V] |
| `m4_lua_boot.json` chunks 112–169 vs package entry order | script resource order | [V] |

---
<small>Source: `docs/engine/Resources.md` in the project repository &middot; generated 2026-10-29.</small>
