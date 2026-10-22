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
- `lua_pushcclosure`: 3,028 distinct C functions before the 60,000-call cap was hit (~frame 5,300); ~80 % of the calls come from two sites (0x14017B02A, 0x14017AF7A) that re-push closures at run time [?]. `lua_setfield`: 4,619 calls. Next capture: cap per caller / registration phase only, and pair each pushed function with the field name it is stored under → native binding map.

## Open [?]
- `dofile` / `Script.LoadLibrary` → `luaL_loadbuffer` is [V live]; the C function behind each (file system read, async queue) is still unread.
- What the two hot `lua_pushcclosure` sites 0x14017B02A / 0x14017AF7A do at run time.
- Which C functions form each Fox/Tpp library table, and how `GameObject`, `Fox`, `Tpp*` tables are populated (luaI_openlib vs manual `pushcclosure` + `setfield`).
- Per-frame calls from C into Lua (`lua_pcall` 0x141A116C0 callers: 255).

## Evidence
| VA | Proves | Tag |
|---|---|---|
| 0x141A112E0 | lua_State top/base offsets, TValue size | [V] |
| 0x141A12150 | TString length +0x10, chars pointer +0x18 | [V] |
| 0x141A17C30 | luaI_openlib: luaL_Reg layout, `_LOADED` | [V] |
| 0x141A178E0 | luaL_loadbuffer → lua_load(getS) | [V] |
| trace_m4_lua_boot_20261022_182621 | boot chunk order (170), 147 openlib calls, 11 metatables, identical over 2 runs | [V live] |

---
<small>Source: `docs/engine/ScriptHost.md` in the project repository &middot; generated 2026-10-22.</small>
