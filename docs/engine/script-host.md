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
- **Script resource** 0x14018BE10: loads a library chunk from a path or an in-memory buffer, `lua_pcall(L, 0, 1, 0)`, and if the chunk returns a table stores it (0x1400F1AA0) under the library name. `Script.LoadLibrary` (0x1400E9A70) requests the resource (0x1400CDF40) and records it in the pending-library map 0x142B65790 keyed by `fox::Path`; `LoadLibraryAsync` (0x1400E9DD0) requests it only if the path is not already in the map; `IsLoadingLibrary` (0x1400E98E0) checks the map. So `start.lua`'s `while Script.IsLoadingLibrary(x) do coroutine.yield() end` is how the boot coroutine waits [I for the wait semantics].

## C → Lua calls per frame [V live]
Capture `trace_m4_lua_pcall_20261022_191611` (config `Tools\FoxTrace\configs\m4_lua_pcall.cfg`, 2 runs, same callers and per-frame rates): ~49,100 `lua_pcall` per run from 249 callers, 430 `lua_resume` from 8. Steady state in free roam (last 3,000 frames):

| Caller | Per frame | What it calls |
|---|---|---|
| 0x141A2E6C0 (Lua `pcall` builtin) | ~4.9 | script-side `pcall`, not a C entry |
| 0x140184650 | 2 | for each of 8 script-block slots (0x142B72C30) whose block is in state 2–3 with flags 0x20 set / 0x01 clear: `table.OnUpdate()` (0 args); slot's id in global 0x1429E4BF0 during the call |
| 0x140ADA420 | 1 | 2 callback slots at 0x142C33368 (registry refs: function + argument), `pcall(f, arg)` — next to `ScriptUpdater.Create` 0x140AD9EA0 [I: ScriptUpdater] |
| 0x140A1CC20 | 1 | vtable 0x1422A9710 slot 16 (class unnamed [?]): when its block is active, `OnSynchronizeSVars(id)` on a flag, then one call per changed var `(name, index)` |

- **Boot pump** 0x140064030: resumes the `start.lua` coroutine (registry ref at owner+0x388) every frame until it finishes (197 resumes per boot), then drops the ref. `coroutine.resume` (0x141A2EAC0) accounts for 216 more during boot.
- Load-time: 0x14018BE10 (library chunks, 162 pcalls per boot), 0x140D5B410 (167, boot) and ~240 rare callers (messages, UI, demo).

## FoxTrace lesson: enable hooks together
FoxTrace installs hooks on its own thread while the game keeps booting. With 16 hooks enabled one by one (each `MH_EnableHook` suspends all threads) the late hooks went live after the registrations they were meant to see (capture 3: `fox_class_add` 0 calls, early stock libs missing, runs disagreeing). Fixed 2026-10-22: create all hooks, then one `MH_EnableHook(MH_ALL_HOOKS)` → capture 4 complete and identical over 2 runs. New arg types for Fox strings: `S` (`char**`), `T` (`fox::String*`), `n`/`N` (`int*`/`double*`); per-hook `skip=<caller VAs>`.

## Open [?]
- Class behind vtable 0x1422A9710 (per-frame `OnSynchronizeSVars`), and the ~240 rare `lua_pcall` callers (message handlers).
- Exact wait semantics of `Script.LoadLibrary` (blocks, or only queues like the async version?) and when the resource system runs 0x14018BE10.
- Which global the declared-vars tables (0x140AE0F70: `__rt`, `__as`, `__index`, `__newindex`) become (`svars` / `gvars` / `mvars`).

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
| trace_m4_lua_pcall_20261022_191611 | per-frame C → Lua callers (OnUpdate ×2, ScriptUpdater, svars sync), boot pump | [V live] |
| trace_m4_lua_boot_20261022_182621 | boot chunk order (170), 147 openlib calls, 11 metatables, identical over 2 runs | [V live] |

---
<small>Source: `docs/engine/ScriptHost.md` in the project repository &middot; generated 2026-10-22.</small>
