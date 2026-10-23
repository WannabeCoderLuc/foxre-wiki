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
- Constructor looks up the `Mission` message channel and subscribes the controller to 24 categories on it (21 named: Marker, Sound, GameObject, Trap, Demo, Timer, Terminal, Weather, Player, Radio, Subtitles, Block, Throwing, Placed, MotherBaseManagement, MotherBaseStage, Network, Video, TppSystem, SupportAttack, SupplyCbox; unnamed StrCode32 0xB913232E, 0xDC05D615, 0x445FE2CA [?]) and creates a block group with one block [V].
- Per-frame update = slot 2 **0x140A1E380** (state of block 0 at block+0x80: 0 empty, 1 processing, 2 loaded, 3 active, 4 [?]):
  - requested mission (0x142A6EFE0) ≠ current (+0x78) or force → new target, clear "loaded" bit;
  - block empty and a target set: wait while the location loader is busy (0x140993FF0: requested location ≠ loaded location, or its block not active); then build the package list (0x140A1D000), hand it to two Quark-table services (+0x2D8, +0x2F8, [?]), make the block depend on the blocks of `EquipCommonBlockGroup`, `CommonStageBlockGroup`, `MBStageCommonBlockGroup` when they exist, and start loading (0x14006DEC0); progress code 0x142C1F8C4 = 1;
  - block loaded (2) and it is the current target: `OnInitialize` step (0x140A1C460) once per frame; result 1 → activate the block (0x14006CFB0, code 5), 2 → unload (code 7), 0 → still running;
  - target changed while loaded/active: unload (code 7) or deactivate first (0x14006D480, code 6).
- Slot 13 **0x140A1D2E0** (block-loaded callback): finds the mission data of the block (0x140A1CB10), builds the `subScripts` table (0x140A1C990), and runs `script.OnAllocate(subScripts)` in a new Lua thread (`lua_newthread` + `lua_resume`); a yield keeps the thread for the next callback; code 2 while running, 3 when done [V].
- Function names are static `fox::String`s: 0x142C1F8E0 = `"OnAllocate"` (initialised from 0x1422A3310), 0x142C1F8F0 = `"OnInitialize"` (0x1422A9598); next to them `"OnUpdate"`, `"OnReload"` [V].
- `mvars`: the mission object (vtable 0x1422A9FB8) constructor 0x140A1E890 and destructor 0x140A1ED90 both call 0x140AE0EE0 = `_G.mvars = {}` (fresh table) [V]. Lua never creates `mvars`.

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
- **Order**: packages in list order; inside a package the scripts run in the **reverse of their stored entry order**, which in every game package seen equals ascending path order: `init.fpkd` stores `mission_main, init_sequence` → live runs `init_sequence, mission_main`; `afgh_script.fpkd` stores `travelPlans … afgh, afgh_luxury_block_list` → live runs the reverse; `f30010.fpkd` stores `mission_main, sound, sequence, radio, orderBoxList, enemy, demo` → live runs the reverse [V static vs live]. Which of the two rules the engine implements is not distinguishable from the data [?].
- `TppSimpleMissionData` (in the mission's own package, e.g. `init_sequence.fox2`): `script` (FilePtr) = `mission_main.lua`; `subScripts` (StringMap of FilePtr) = `sequence`, `enemy`, `demo`, `radio`, `sound`, `photo` … → the `subScripts` table handed to `OnAllocate` / `OnInitialize` maps each key to that script's returned table [I: table content; the keys are the data's].

## Boot sequence (live chunks 112–169)
| Live chunks | Trigger | Packages (Lua resources) |
|---|---|---|
| 112–113 | `start.lua` → `TppVarInit.StartInitMission()` → `TppMission.Load(1, force)` | location INIT: `tpptest/.../empty.fpk`; mission 1: `gz_pause_key_setting_data.fpk`, `init.fpk` (init_sequence, mission_main) |
| 114–122 | UI parameter tables (`emblem_list`, `mbdvc_*` ×2) | not a package load: UI native code [?] (`ScriptHost.md`) |
| 123–125 | pre-title UI (0x14085C8C0, state 4) calls `TppVarInit.StartTitle` [V]; save past the hospital → heli space 40010 in afgh | location afgh: `afgh.fpk` (no scripts) + common `afgh_common.fpk` (fx_mtr def/rain/underwater) |
| 126–144 | same | mission 40010: `heli_common_script`, `title_sequence`, `heli_ui`, `mis_com_helicopter`, `afgh_script` (14 location scripts), `h40010_area` (photo, radio, mission_main), 2 coloring packs |
| 145–166 | title CONTINUE → `TppMission.Load(30010, 40010)` | mission 30010: `afgh_script`, `mis_com_helicopter`, `mis_com_afgh`, decoy, `mis_com_order_box` (order_box_block), `f30010.fpk` (demo … sound, mission_main), 2 coloring packs |
| 167–169 | mission scripts → `ScriptBlock.Load` | reinforce / quest / animal script blocks [?] |

**Engine host result (`Engine\tests\test_m5_mission_load.py`):** with the two later requests made at the native boundary, the host loads **46 chunks in exactly the live order (live 112–166 minus the 9 UI tables)**, no Lua error; the block events (location INIT → mission 1 → location afgh + common → mission 40010 → mission 30010 without location reload) match. Missing for the M5 gate: the UI tables and the 3 script blocks.

## Open [?]
- Script blocks (`ScriptBlock.Load`, 0x140183B50; 8 slots at 0x142B72C30, `OnUpdate` caller 0x140184650): reinforce / quest / animal chunks 167–169. Needs the mission scripts' `OnAllocate`/`OnInitialize` to run to completion → M4 record/replay of the natives they wait on.
- The location loader's update function and the exact frame order between location, common block and mission block.
- The two Quark-table services that receive the mission package list (+0x2D8, +0x2F8 of the table at QuarkSystemTable+0x98).
- FSTB beyond the common-package header.
- `Mission.RequestToReload` (0x140A1FA40) and `TppMission.RequestLoad` (reload without location change).

## Evidence
| VA | What it shows | Tag |
|---|---|---|
| 0x140A1FB60 / 0x140A1FBD0 | `Mission.LoadLocation` / `LoadMission`: read `opts.force`, latch vars codes | [V] |
| 0x140993FA0 / 0x140993F60 / 0x140993FF0 | location request latch / requested flag / "location busy" test | [V] |
| 0x140A1D610 | mission request latch (0x142C1F8B1 force, 0x142A6EFE0 code) | [V] |
| 0x140994670 / 0x140A1DEE0 | `Set{Location,Mission}PackagePathFunc`: registry refs 0x142C01120 / 0x142C1F8C0 | [V] |
| 0x140A1D000 | calls the mission Lua function with the code under `lua_pcall`, table/string result → path list | [V] |
| 0x140A1E380 | mission block controller update (vtable 0x1422A9710 slot 2), state machine above | [V] |
| 0x140A1D2E0 / 0x140A1C460 | `OnAllocate` / `OnInitialize` coroutines with `subScripts` | [V] |
| 0x140A1B760, 0x140A1D260, 0x140A1CAC0 | controller ctor (message subscriptions, block group); DataBody slots that build it | [V] |
| 0x140A1E890 / 0x140A1ED90 → 0x140AE0EE0 | mission object ctor/dtor reset `mvars = {}` | [V] |
| 0x14085C8C0 | pre-title sequence state 4 calls Lua `TppVarInit.StartTitle` (strings 0x142240FB0/0x142240FC0) | [V] |
| 0x1405CEDA0 / 0x1405CEE80 | coloring pack list | [V] |
| `fox_edb.json` | `TppSimpleMissionBlockControllerData` (name +72, blockSizeInByte +120), `...DataBody` size 96, `TppSimpleMissionData` (script, subScripts) | [V] |
| `m4_lua_boot.json` chunks 112–169 vs package entry order | script resource order | [V] |

---
<small>Source: `docs/engine/Resources.md` in the project repository &middot; generated 2026-10-23.</small>
