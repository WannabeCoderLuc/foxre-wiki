# Script host

Clean-room spec for `Engine\script\` (roadmap M4). Tags: [V] read in the exe / seen live this pass, [I] inferred, [?] open.
Started 2026-10-22; static facts first, live capture section below.

## Lua runtime: stock Lua 5.1 with one layout change [V]
The game links Lua 5.1 (API at 0x141A10CC0–0x141A17C30, addresses from the IHHook address table, each re-read here):

| Function | VA | What the code shows |
|---|---|---|
| `lua_gettop` | 0x141A112E0 | `(L+0x10 top − L+0x18 base) >> 4` → `lua_State.top` +0x10, `.base` +0x18, `TValue` 16 B |
| `lua_settop` | 0x141A11F70 | fills new slots with `tt = 0` at TValue+8 (nil); negative index relative to top |
| `lua_isstring` | 0x141A11440 | `tt − 3 ≤ 1` → number 3, string 4 (stock numbering) |
| `lua_touserdata` | 0x141A122C0 | tt 2 (light userdata) → value; tt 7 (full userdata) → `Udata + 0x28` (stock header size) |
| `lua_tolstring` | 0x141A12150 | tt 4: length = `*(TString+0x10)`, chars = **`*(TString+0x18)` (a pointer)**; other types converted via `luaV_tostring` 0x141A270E0 |
| `lua_setfield` | 0x141A11E00 | `strlen(k)` → `luaS_newlstr` 0x141A233D0 → key TValue (tt 4) → settable with top−1 |
| `luaL_loadbuffer` | 0x141A178E0 | `lua_load(L, getS 0x141A16BA0, {buff, size}, name)` (`lua_load` 0x141A11500) |
| `luaI_openlib` | 0x141A17C30 | counts the `luaL_Reg` array (16-B `{name, func}` entries, NULL-terminated); `luaL_findtable(REGISTRY (−10000), "_LOADED", 1)`; then `lua_getfield(−1, libname)`, `lua_type == 5` (table) check |
| `luaL_newmetatable` | 0x141A17B70 | stock (registry table per type name) |
| `lua_pushcclosure` | 0x141A11770 | C function + upvalues |

**Engine consequence:** everything is stock Lua 5.1 semantics except the string object: `TString` keeps its characters behind a pointer at +0x18 instead of inline after the header. That only matters for native code reading game memory (FoxTrace, IHHook); a clean-room host can use unmodified Lua 5.1 (lupa) because Lua-visible behaviour is unchanged [I].

## Boot scripts (static)
Vanilla files (1.0.15.4, `EXTRACTED_DATA`): `master/0/00.dat/init.lua` (190 lines) = `data1.dat/init.lua` (identical bytes), `Tpp/start.lua` (214 lines, identical in both), `data1.dat/Tpp/Scripts/System/start2nd.lua` (6 lines). `init.lua` runs `dofile` on the per-platform graphics init (`Fox/Scripts/Gr/gr_init*.lua`) and shader tables (`shaders/dx11/*_dx11.lua`); `start.lua` brings up the Tpp script libraries; `TppMain.lua` / `TppDefine.lua` are in `tpp/script/lib/`. Load order and who calls which file: live capture below.

## Live capture: boot order + registrations (FoxTrace 2)
Config `Tools\FoxTrace\configs\m4_lua_boot.cfg` (hooks `luaL_loadbuffer`, `luaI_openlib`, `luaL_newmetatable`, `lua_pushcclosure`, `lua_setfield`), profile engine-clean, `trace_capture` 2 runs (2026-10-22, `Memory\research\trace_m4_lua_boot_20261022_182621\`), boot 84–86 s to f30010. All hooks installed (`MH_OK`); game restored to mod-baseline after. Fixture: `Engine\tests\fixtures\m4_lua_boot.json`.

**Every script chunk goes through `luaL_loadbuffer`** [V live]: 463/471 calls per run, chunk names `@<path>` (so `dofile` / `Script.LoadLibrary` read the file through Fox's file system and compile it with `luaL_loadbuffer`; `luaL_loadfile` is not used) plus inline strings (`Fox.SetJobExecutorCount( 14 )`).

- Vanilla chunks (IH's `/ih/`, `mod/modules` and IHH pipe snippets removed): **170 per run, same set; same order except positions 37–39** (`TppLocation.lua` swaps with the `mbdvc_map_*` UI tables — `Tpp.lua` is loaded with `Script.LoadLibraryAsync`) [V live].
- Boot order (first chunks): `Fox/Scripts/Classes/Entity.lua`, `Scene.lua`, `Pad.lua` → `ui/Script/emblem_list.lua` → `Fox.SetJobExecutorCount( 14 )` → **`init.lua`** → `gr_init_dx11.lua` → 3 DX11 shader tables → **`Tpp/start.lua`** → `TppShadersNoLnm_dx11.lua` → sound chara scripts → `TppUiBootInit.lua` … equip/enemy parameter tables → **`Tpp.lua`** → `TppDefine.lua` → `TppMath`, `TppSave`, `TppLocation` (async window), `TppSequence`, `TppWeather` … `TppMission`, `TppStory`, `TppDemo`, `TppEnemy` … (full list in the fixture). Matches the static `start.lua` order of `dofile` / `Script.LoadLibrary` calls.
- IH hooks in after `init.lua` (`InfInit.lua`, `InfCore.lua`, then 119 IH chunks) — mod additions, not engine behaviour.

**Library registration** [V live]: 147 `luaI_openlib` calls, identical name sequence in both runs: the stock libs (`_G`, `coroutine`, `package`, `table`, `io`, `os`, `string`, `math`, `debug`, `bit`), then Fox/Tpp libraries in boot order — `foxmath`, `Vector3`, `Vector4`, `Quat`, `Matrix3`, `Matrix4`, `WideVector3`, `Color`, `File`, `FoxGameFrame`, `PlatformConfiguration`, `AssetConfiguration`, `HidDriver`, `NtDaemon`, `Geo`, `Gr`, `SoundCoreDaemon`, `Nav`, `NavTactical`, `GameCore`, `GkTacticalService` … `TppSoldier2`, `TppHostage2`, `TppEquip` (×7), `HighSpeedCamera`/`TppCollection`/`TppPlaced`/`TppShell`/`TppBullet`/`TppDecoy`/`CaptureCage` (×3) (136 named + 11 `luaL_register` into the table on the stack). 28 `luaL_Reg` arrays lie in the image (static `{name, func}` tables, readable with `re_bytes`); the others are built on the heap (address differs per run). `IHH`, `IhkCharacter`, `IhkBuddy`, `IhkVehicle` are IHHook's.

- Metatables (`luaL_newmetatable`, 11): `_LOADLIB`, `FILE*`, `fox.Vector3`, `fox.Vector4`, `fox.Quat`, `fox.Matrix3`, `fox.Matrix4`, `fox.WideVector3`, `fox.Color`, `fox.File`, `LightUserData`.
- `lua_pushcclosure`: the first capture hit its 60,000-call cap at ~frame 5,300 because ~80 % of calls come from Fox's `pairs`/`ipairs` (below). With those two call sites skipped: 8,080 calls per boot, identical in both runs.

## Native bindings: four registration paths (binding map) [V]
Fixture `Engine\tests\fixtures\m4_lua_bindings.json` (`{library: {name: VA}}`): **399 game libraries, 5,532 bindings, 2,707 distinct C functions**, 2,286 enum values, 417 storage addresses. Capture `trace_m4_lua_bindings4_20261022_190858` (2 runs, identical apart from heap addresses), config `Tools\FoxTrace\configs\m4_lua_bindings.cfg`, distiller `Tools\FoxTrace\distill_bindings.py`, test `Engine\tests\test_m4_bindings.py` (static oracle against the exe). Only the main `lua_State` registers C functions; the other states are script coroutine threads that only set var fields.

| Path | Entry points | Where the name goes | Libraries |
|---|---|---|---|
| Stock `luaI_openlib` / `luaL_register` | 0x141A17C30; static `luaL_Reg` arrays (28 in the image) or arrays built on the heap | `lua_setfield` | stock libs, `foxmath`, `Vector3`…`Color`, `Nav`, `HidDriver`, `AssetConfiguration`, `Geo`, `Gr` … (147 calls) |
| Fox table builder | `begin(L, name, a, b, hashedKeys)` 0x141A158E0 (140 callers), `sub(parent, name, …)` 0x141A159C0 (nested, e.g. `Vehicle.type`), `set(builder, L, idx, name)` 0x141A14650, `end(builder)` 0x141A15760; current builder in global 0x142C6C038 | raw table set (`luaH_set` / `luaH_setnum`); with `hashedKeys` the key is **StrCode32 & 0xFFFFFFF as a number**, so no `lua_setfield` and no string key | most Tpp libraries (`TppGameObject`, `Player`, `TppUiCommand`, `vars`, enums …) |
| Fox class tables | `begin(ctx, holder, classInfo)` 0x1400F7990 → 0x1400F7720 (looks the table up in `_G` by the class name, `fox::String` at classInfo+200; creates it with closures 0x1400F66B0 / 0x1400F68C0 and a metatable); `add(ctx, name, fn)` 0x1400F79D0 | Fox key setter 0x141A13B80 (`{char*, len, hash}`, `luaV_settable`) | `Fox`, `Script`, `GameObject`, `GkEventTimerManager`, entity classes … (233 classes, 470 functions) |
| Direct `lua_setfield` | `lua_pushcclosure` + `lua_setfield` in one C function | `lua_setfield` | `_G.pairs`/`ipairs` (Fox), class `__call` constructors, declared-vars metatables |

- **Thunks** [V]: builder functions with a C++ target are pushed as closure 0x141A154D0 with the target as a light-userdata upvalue (`impl` section of the fixture); class functions as closure 0x1400F6630 whose upvalue is a full userdata holding the target (called as `fn(ctx)`, `ctx+8 = L`). The fixture records the target as the binding VA.
- **Constants** [V]: builder constants are closures, not numbers: 0x141A13CF0(builder, name, int*) → closure 0x141A13E40 returning the integer, 0x141A13DA0(…, double*) → 0x141A13E90 returning a number (`values` section, e.g. `TppGameObject.GAME_OBJECT_TYPE_PLAYER2 = 0`, `SOLDIER2 = 2`). Builder tables get `__index` / `__newindex` closures 0x141A14020 / 0x141A143C0.
- **`vars`** [V]: 394 entries, each a getter closure (0x1409AA9B0, 0x1409AAB80, 0x1409AAA90, 0x1409AABF0 … by type) with the address of the variable in the global save block (0x142C01350…0x142C1690C) as upvalue (`impl.vars`).
- **Stubs** [V]: 74 bindings point at one shared empty function 0x141C658E0 (stripped in the release build; identical-code folding gives it the symbol `tpp::ef::OutOfMissionRangeEffectLua::SetupInterp`), incl. `print`, `Fox.Log`/`Warning`/`Error`, `PlatformConfiguration.*`, `TppNetworkUtil.*`, `debug.debug`. IHHook hooks exactly this function (`l_StubbedOut`) and replaces `_G.print`.
- **Fox `pairs` / `ipairs`** [V]: registrar 0x14017ADC0 overwrites the stock globals (`lua_setfield(LUA_GLOBALSINDEX)`) with 0x14017AFF0 / 0x14017AF40: a table goes to the stock iterator (`lua_next` 0x14017B0A0 / ipairs_aux 0x141A2EF50); a userdata whose registry has `LuaProperty` (Fox array/map properties) gets iterator 0x1401A3C70 / 0x1401A31A0 (errors `illegal property for 'pairs'`, `is not array !`). These are the two run-time `pushcclosure` sites 0x14017B02A / 0x14017AF7A: every `pairs()`/`ipairs()` call in script pushes a fresh iterator closure.
- **Static cross-check**: all 28 in-image `luaL_Reg` arrays (256 functions) equal the live bindings; `Script` equals the static registrar 0x1400E9460 (`GetScript`, `ReloadAll`, `DebugSetAlwaysLoadingFileEnabled` (stub), `LoadLibrary` 0x1400E9A70, `LoadLibraryAsync` 0x1400E9DD0, `IsLoadingLibrary` 0x1400E98E0).

**Engine consequence:** the Lua host needs (a) the stock libs, (b) builder-style registration that stores StrCode32-hashed keys for hashed tables and exposes constants through `__index`, (c) class tables with `__call` constructors, (d) Fox `pairs`/`ipairs` that also iterate property userdata, (e) no-op stubs for the 74 stripped functions. The fixture is the API surface to stub in `Engine\script\` [I].

## Chunk loading: C side [V]
- **Loader** 0x141A18520(L, buf, size, key, chunkname): 0x141A182B0 decodes buffers whose first byte is 0x1B or 0x1C (XOR with a rolling 8-byte key `~key`, key = 0x14006B4D0(file name without directory); 0x1C additionally inflated by 0x141A37520), then `luaL_loadbuffer`. Plain text passes through unchanged.
- **Fox dofile** 0x14006BC10(L, path): reads the file through the Fox file system, strips a UTF-8 BOM, chunk name `@<path>` (format `@%s`), loads with the loader above. Callers: boot driver and the script-resource loader. The Lua global `dofile` stays stock (`luaL_loadfile`, 0x141A2E450); vanilla boot chunks all come through the Fox path (`@…` names, caller 0x141A18582); `loadstring` (0x141A2E324) is used by IH.
- **Boot driver** 0x140063C60: creates the Lua environment, runs an optional configured script, then `init.lua` (both synchronously), then `<app>/start.lua` (format `%s/%s`) **as a coroutine** (`lua_newthread` + `lua_resume`); a yield (status 1) keeps the thread for later resumption. Matches the live order init.lua → … → Tpp/start.lua.
- **Script resource** 0x14018BE10: loads a library chunk from a path or an in-memory buffer, `lua_pcall(L, 0, 1, 0)`, and if the chunk returns a table stores it (0x1400F1AA0) under the library name. `Script.LoadLibrary` (0x1400E9A70) requests the resource (0x1400CDF40) and records it in the pending-library map 0x142B65790 keyed by `fox::Path`; `LoadLibraryAsync` (0x1400E9DD0) requests it only if the path is not already in the map; `IsLoadingLibrary` (0x1400E98E0) checks the map. So `start.lua`'s `while Script.IsLoadingLibrary(x) do coroutine.yield() end` is how the boot coroutine waits. `LoadLibrary` is synchronous: `start.lua` uses each library on the next line, and in the live order no `LoadLibrary` chunk ever moves (only the async ones do) [V live + usage]. A library loads once (`TppDefine` is in `Tpp.requires` and loaded again by `start.lua`, but appears once live) and, after its chunk returns a table, the engine loads the table's `requires` list in order (`Tpp.requires` = live chunks 33–74) [V live].

## C → Lua calls per frame [V live]
Capture `trace_m4_lua_pcall_20261022_191611` (config `Tools\FoxTrace\configs\m4_lua_pcall.cfg`, 2 runs, same callers and per-frame rates): ~49,100 `lua_pcall` per run from 249 callers, 430 `lua_resume` from 8. Steady state in free roam (last 3,000 frames):

| Caller | Per frame | What it calls |
|---|---|---|
| 0x141A2E6C0 (Lua `pcall` builtin) | ~4.9 | script-side `pcall`, not a C entry |
| 0x140184650 | 2 | for each of 8 script-block slots (0x142B72C30) whose block is in state 2–3 with flags 0x20 set / 0x01 clear: `table.OnUpdate()` (0 args); slot's id in global 0x1429E4BF0 during the call |
| 0x140ADA420 | 1 | 2 callback slots at 0x142C33368 (registry refs: function + argument), `pcall(f, arg)` — next to `ScriptUpdater.Create` 0x140AD9EA0 [I: ScriptUpdater] |
| 0x140A1CC20 | 1 | vtable 0x1422A9710 slot 16, the mission-script owner (the mission block controller, `Resources.md`; its constructor 0x140A1B760 subscribes it to 24 message categories: Mission, Block, Demo, GameObject, Marker, Player, Radio, Sound, Timer, Weather …) [V static; class name [?]]: when its block is active, `OnSynchronizeSVars(id)` on a flag, then one call per changed var `(name, index)` |

- **Boot pump** 0x140064030: resumes the `start.lua` coroutine (registry ref at owner+0x388) every frame until it finishes (197 resumes per boot), then drops the ref. `coroutine.resume` (0x141A2EAC0) accounts for 216 more during boot.
- Load-time: 0x14018BE10 (library chunks, 162 pcalls per boot), 0x140D5B410 (167, boot) and ~240 rare callers (messages, UI, demo).

## More registration paths: plain values [V static]
Two paths store plain values instead of closures, so FoxTrace's binding capture does not see them; `Tools\static_lua_consts.py` reads them from the exe into `Engine\tests\fixtures\m4_lua_consts.json`:

- **pushnumber + setfield**: `lua_pushnumber(k)` + `lua_setfield(-2, name)` inside a registrar. Example: the `Pad` class registrar 0x14043AA70 fills the global `fox` with 140 pad/key constants (`fox.PAD_A = 1`, `PAD_B = 2`, `PAD_X = 0`, `PAD_Y = 3` …; values come from `movsd xmm1, [const]`, `movaps xmm1, xmm14/15` or `xorps`). Also `TppPadType` (4), `TppBuddyDog` (7), `GsRoute.ROUTE_ID_EMPTY`, `foxmath.PI = 3.1415927` (float).
- **enum arrays**: a stack array of 16-B `{int value, char* name}` entries, then a loop `lua_pushlstring(name)` + `lua_pushnumber(value)` + `lua_settable(-3)` into the global named by `lua_getfield(GLOBALS, name)` (created when missing). `TppEquip` 2,439 values, `TppDamage` 523, `TppCollection` 65 (registrar 0x140A0AA60; `TppTerminal.lua` reads `TppCollection.TYPE_*` at load, before `TppCollection`'s functions are registered by `luaI_openlib` at frame 222 — the table exists earlier because of this array).
- **Constant return tables**: `TppScriptVars.GetProgramVersionTable` (0x1409AA780) returns `{[0]=0, [1]=0, [2]=0, [4]=1, [8]=3, [16]=0, [32]=5, [64]=0, [128]=1}` (category bit → program save version).
- **Declared vars** [V static]: `TppScriptVars.DeclareGVars` 0x140AE1C10 / `DeclareSVars` 0x140AE1C70 → 0x140AE0F70 build the globals **`gvars`** and **`svars`** (name pointers 0x142A7EC30 / 0x142A7EC38; `mvars` follows in the same table) from the script's declaration list (`name`, `type`, `value`, `arraySize`, `save`, `sync`, `category`); `DeclareSVars` runs once.

## Engine-side script loads [V]
Some chunks are loaded by natives, not by Lua: `TppSoundDaemon{…}` (constructor 0x14096F690) loads `SoundTppPlayer/Soldier/Animal.lua`; `UiDaemon.SetExecLuaFile(path)` runs its file a frame later (`TppUiPrefetchTexture.lua`); `TppCassetteTapeInfo.Setup()` → `PreinstallTape.lua` (0x140975580) next frame [I for the frame]; `Player.RegisterScriptFunc(path, …)` loads `TppPlayer2CallbackScript.lua` immediately. A UI object (vtable 0x14227F940, 0x140969A60) loads the `mbdvc_map_*_parameter.lua` tables through the script resource; `mbdvc_pause_help_table.lua` likewise — trigger [?].

## Engine host: `Engine\script\` (M4 module)
`host.py` (lupa Lua 5.1) + `vfs.py` (extracted archives, patch first; 0x1B/0x1C decode via `formats.fpk`) + `foxmath.lua`. Built from this spec and the three fixtures, no game code:

- every library appears at the boot point the game registers it (`registered_after_chunks`); functions are counted stubs, the 74 stripped ones no-ops; class tables answer unknown members with stubs and are callable; `<Lib>.GetInstance` returns a per-library proxy [I]; `vars`/`cvars` are plain storage (scalars 0, other names 0-based arrays) [I];
- natives: `Script.LoadLibrary*`/`IsLoadingLibrary` (sync, load-once, `requires`), Fox `dofile`/`loadfile`, `Fox.StrCode32`, `bit.*`, `DeclareGVars/SVars`, `GetProgramVersionTable`, the engine-side loads above, and four environment answers fixed by the live boot (`Fox.GetPlatformName` = Windows, `GrTools.GetDeviceName` = directx11, `AssetConfiguration.IsDiscOrHddImage` = true, `TppSystemUtility.GetCurrentGameMode` = TPP);
- boot = class scripts → `init.lua` → `Tpp/start.lua` coroutine resumed per frame (deferred loads, then async libraries, then resume).

**Result (test `Engine\tests\test_m4_script_host.py`):** the boot runs to the end in 34 frames with **no Lua error** and loads **108 chunks in exactly the live order** (live chunks 0–111 minus the 4 UI tables above). API surface touched: 346 distinct functions, 15 native, 3 stripped, 328 stubs (5 %). The live boot continues with the init mission (`init_sequence.lua`, `mission_main.lua`, location scripts): those come from mission packs loaded by the block system — next step.

## Record/replay of native answers (M4 gate, started 2026-10-23)
- **Thunks** [V static]: class functions run through 0x1400F6630 (`target = *(void**)lua_touserdata(L, upvalueindex(1))`, called as `target(ctx)`), builder functions with a C++ target through 0x141A154D0 (`target = lua_touserdata(L, upvalueindex(1))`, ctx = `{L, gettop, nret}`); both return the result count. Most bindings are plain `lua_CFunction`s and bypass both.
- **FoxTrace 3 `luaret`** (`Tools\FoxTrace\foxtrace.cpp`): typed detour per hook (up to 1024); kinds `c` / `b` for the two thunks, `d` for a `lua_CFunction` itself (calls whose argument does not look like a `lua_State` pass through). Logs target VA, arguments and the returned stack values for the first K calls per (target, argument list). Generator `Tools\FoxTrace\make_luaret_cfg.py` (host stubs + their libraries), distiller `Tools\FoxTrace\distill_returns.py` → `Engine\tests\fixtures\m4_lua_returns.json`.
- Captures (profile engine-clean, cold boot → f30010, 45 s): `trace_m4_luaret_20261023_110720` (thunk hooks, 387 returns per run) and `trace_m4_luaret_direct_20261023_111747` (2 thunk + 1,022 direct hooks from `configs\m4_luaret.cfg`, 2,919 returns per run, 427 hooks hit); each 2 runs identical → **536 binding names, 534 stable** in `m4_lua_returns.json`. 12 hooks did not install (names > 63 chars broke the config tokenizer; fixed in the parser after the run). The first attempt crashed the game for the same reason (VA parsed as 0 → `EnableAll` read an unmapped target; read now SEH-guarded).
- Host (`ScriptHost(replay=load_returns())`): a stubbed function with recorded answers replays them per argument list in call order, then repeats the last; userdata results become the host's stub proxy, table results an empty table [I]; `GetInstance` stays a proxy. Test `test_m4_replay.py`.
- **Coverage of the M5 scenario** (boot → init → title 40010 → f30010 + 300 frames): without replay 360 functions called, 20 native, 3 stripped, 337 stubs (6.4 % answered); the f30010 `OnAllocate` waits forever in `TppMission.WaitFinishMissionEndPresentation` on `TppUiCommand.IsEndMissionTelop()` (stub nil; live answer `true` [V]). **With replay: 387 called, 20 native, 319 replayed, 6 stripped, 48 stubs (89.1 % answered); `OnAllocate` and `OnInitialize` finish for 40010 and 30010.**
- ~~Remaining failure: `Vehicle.svars{}`~~ → native now (below). Table-valued natives in general are still recorded as "a table" only.
- **Second capture (2026-10-23, M5):** `make_luaret_cfg.py --replay` runs the host with the first recording, so it reaches further, and hooks every `ScriptBlock.*` native (per=64) plus `luaL_loadbuffer` (chunk loads interleaved = M5 ground truth), the stubs still called, natives the loaded chunks reference statically, then the rest of their libraries (`configs\m5_luaret.cfg`, 1,011 direct hooks). Capture `trace_m5_luaret_20261023_115514` (2 runs, same chunk order up to the end of the boot); `distill_returns.py --merge` keeps the first recording → **663 binding names (659 stable)**. `ScriptBlock.*` calls are not distilled (implemented natively).
- **Coverage now** (M5 gate scenario: save image, 1,900 frames after f30010 loads): 538 functions called, 35 native, 457 replayed, 7 stripped, 46 stubs → **92.8 % answered**; f30010 runs `OnAllocate`, `OnInitialize`, the mission-prepare sequence and `OnMissionCanStart` with no Lua error. Left: 40010's `DataIdentifier` locator (world data), class-instance stubs (`UiDaemon:`, `PhDaemon:`, `GrTools:`).

### Natives added for the mission start (2026-10-23)
| Native | VA | Host |
|---|---|---|
| `Vehicle.svars{instanceCount=}` | 0x140A27780 | 9 declarations from the static table 0x1422ABB30 (16-byte rows: name, per-instance count, extra, type, category, flags save/sync/wait); `arraySize = count × (instanceCount+1) + extra` (absent or 60 → 60; > 60 → no result), value 0.0 [V] |
| `Fox.PathFileNameCode32(path)` | 0x140179B40 | low 32 bits of the path hash without extension (PathCode64 minus type bits); non-string → 0 [V data: 385 LBA footer pairs (locator StrCode32, dataSet code) over the afgh `.lba` files match `afgh_gimmick.lua`'s dataSet paths] |
| `TppScriptVars.SetSVarsNotificationEnabled(b)` | 0x140AE2870 | global 0x142A7EC48, copied into svars +0x30 bit 0 [V] |
| `TppScriptVars.LoadVarsFromSlot(slot, groupBits, categoryMask)` | 0x140A224B0 | save boundary: copies saved values of the declared vars of the selected groups (GVARS 4, SVARS 8) whose declared category is in the mask, from one recorded save image (`Engine\tests\fixtures\m5_save_image.json`, live dump) [I: slots not separated] |
| `TppSoldier2CommonBlockController.SetPackagePathWithPrerequisites` / `IsReady` | 0x1409FA460 / 0x1409FA3D0 | `Resources.md` |
| `ScriptBlock.*` | 0x1401839F0 … | `Resources.md` "Script blocks" |
| `Time.GetRawElapsedTimeSinceStartUp` / `GetFrameIndex` | 0x140184A10 / 0x140184980 | time object +0x30 (raw seconds); host clock 1/60 s per frame [I: FoxTrace measures 59.5 jobs/s] |
| `Mission.CanStart` / `GetTextureLoadedRate` | 0x140A1F9F0 / 0x140A1F980 | start-condition object / texture-streaming rates; host: true / 0.0 (no refrainers, no streaming) [I] |

- **svars change log** [V]: svars object +0x20 entries `{u16 var, u16 index}`, +0x2C count (max 0x80), +0x30 bit 0 = notifications on. A write is logged for vars declared `notify` (declaration key 0x1422E31A8; `sync` forces it, 0x140AE0F70) while enabled (0x140AE0E5E); the mission controller drains it each frame as `OnChangeSVars(subScripts, name, index)` before `OnUpdate` (0x140A1CC20). This is how `svars.seq_sequence = …` (a `sync` var) enters a TppSequence sequence. Engine: only changed values are logged [I]. **Scope:** implemented only as far as TppSequence needs it to enter `Seq_Mission_Prepare` (the one consumer the M5 gate exercises). Not done, open [?]: the second change path 0x140AE29D0 (compares values; network sync?), `OnSynchronizeSVars` (controller flag +0x44 bit 0x10), the 0x80 overflow behaviour, the runtime flag 0x40 ↔ `notify` mapping, and every other `OnChangeSVars` consumer in `Tpp._requireList`.
- **Declaration keys** (0x140AE0F70) [V]: `name`, `type`, `value`, `arraySize` (default 1), `save` (bit 0), `sync` (bit 1, also sets `notify`), `wait` (bit 2), `notify` (bit 3), `category` (default 0x80).
- **svars lifetime**: `Resources.md` (mission object).
- **Late library registration**: `HighSpeedCamera`, `TppCollection`, `TppPlaced`, `TppShell`, `CaptureCage` appear between live chunks 113 and 114, i.e. after the init mission package's scripts and before its `OnAllocate`; the registering code is reached only from obfuscated code (.xdata 0x1477E294A / 0x1478070E0), so the host registers them on that event (`MISSION_BLOCK_LIBS_AT`) [V live position; event [I]].
- Host detail: lupa returns a tuple for a Python-side globals lookup made while a Lua coroutine is running; natives that need Lua helpers cache them at start-up (`ScriptHost.var_cat`, `restore_var`).

## FoxTrace lesson: enable hooks together
FoxTrace installs hooks on its own thread while the game keeps booting. With 16 hooks enabled one by one (each `MH_EnableHook` suspends all threads) the late hooks went live after the registrations they were meant to see (capture 3: `fox_class_add` 0 calls, early stock libs missing, runs disagreeing). Fixed 2026-10-22: create all hooks, then one `MH_EnableHook(MH_ALL_HOOKS)` → capture 4 complete and identical over 2 runs. New arg types for Fox strings: `S` (`char**`), `T` (`fox::String*`), `n`/`N` (`int*`/`double*`); per-hook `skip=<caller VAs>`.

## Open [?]
- Mission load: answered 2026-10-23 in `Resources.md` (location loader, mission block controller, script resources, `OnAllocate`/`OnInitialize` coroutines, pack-scoped VFS).
- Class behind vtable 0x1422A9710: the mission block controller created by the `TppSimpleMissionBlockControllerData` DataBody (`Resources.md`) [V identity; class name "TppSimpleMissionBlockController" [I]].
- UI parameter tables (`mbdvc_map_*_parameter.lua`, `mbdvc_pause_help_table.lua`): (re)loaded by slot 0 (0x140969A60) of the object with vtable 0x14227F940, built inside a large UI owner (vtable 0x14226ED40, ctor 0x14091FC60, created from 0x140920F90); what triggers the two reloads after the init mission (live chunks 114–122) is still open. `emblem_list.lua` comes from 0x1405D0BF0 (emblem setup) [V static].
- Return values of the stubbed functions the boot touches (the host returns nil): record/replay capture with FoxTrace 3 `luaret` hooks (M4 gate).

## Evidence
| VA | Proves | Tag |
|---|---|---|
| 0x141A112E0 | lua_State top/base offsets, TValue size | [V] |
| 0x141A12150 | TString length +0x10, chars pointer +0x18 | [V] |
| 0x141A17C30 | luaI_openlib: luaL_Reg layout, `_LOADED` | [V] |
| 0x141A178E0 | luaL_loadbuffer → lua_load(getS) | [V] |
| 0x141A158E0 / 0x141A14650 / 0x141A15760 | Fox table builder begin / set / end; hashed keys StrCode32 & 0xFFFFFFF | [V] |
| 0x1400F79D0 / 0x1400F7720 | class binder add / class table lookup | [V] |
| 0x14017ADC0 | Fox pairs/ipairs replace the globals | [V] |
| 0x141A18520 / 0x141A182B0 | chunk loader, 0x1B/0x1C XOR (+inflate) decoding | [V] |
| 0x140063C60 | boot driver: init.lua, start.lua as coroutine | [V] |
| trace_m4_lua_bindings4_20261022_190858 | binding map, 2 identical runs | [V live] |
| 0x14043AA70 / 0x140A0AA60 | plain-value registrars: `fox` pad constants, enum arrays (`TppCollection`) | [V] |
| 0x140AE1C10 / 0x140AE1C70 | DeclareGVars / DeclareSVars build `gvars` / `svars` | [V] |
| 0x1409AA780 | GetProgramVersionTable constant table | [V] |
| test_m4_script_host.py | host boot: 108 chunks in live order, no error | [V] |
| trace_m4_lua_pcall_20261022_191611 | per-frame C → Lua callers (OnUpdate ×2, ScriptUpdater, svars sync), boot pump | [V live] |
| trace_m4_lua_boot_20261022_182621 | boot chunk order (170), 147 openlib calls, 11 metatables, identical over 2 runs | [V live] |

---
<small>Source: `docs/engine/ScriptHost.md` in the project repository &middot; generated 2026-10-23.</small>
