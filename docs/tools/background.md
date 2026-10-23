# Background

Condensed 2026-10-21 from the 2026-10-13/14 reports (originals in `Quarantine\Cleanup_2026-10-21\Memory\research\`). Tags: [V] verified, [D] game data, [W] wiki/community, [I] inferred, [?] unknown.

## 1. Game and engine facts
- Target: MGSV:TPP PC Steam **1.0.15.4 EN** ("day3900", released 2026-06-09), `mgsvtpp.exe` x64 D3D11, image base 0x140000000. Steam exe and `GameBackup` exe are byte-identical. **Denuvo Anti-tamper**: no exe patching, no downgrader, no Steam-less/prototype builds, offline single player only.
- One exe holds engine + game. Fox modules (FoxCore, Gr/Grx, Anim, Ph/Phx, Nav/Navx, Sd, Ui, Demo, Geo/Geox, FoxQuark) and game modules (TppGameCore, TppGameKit, TppMotherBaseCore, TppSound, TppUi …).
- Data: QAR archives (`master/chunk0-4.dat`, `texture0-4.dat`, `data1.dat`, patches `master/0/00.dat`/`01.dat`) → `.fpk/.fpkd` packages → ~100 formats (`.fox2` DataSets, `.fmdl`, `.ftex(s)`, `.mtar/.gani`, `.nav2`, `.frt`, Wwise `.sbp/.bnk/.wem`, `.mog`, `.parts`, `.tgt`, …). Extracted copy: `EXTRACTED_DATA\…\Build_1_0_15_4\Current\`.
- Logic is largely Lua 5.1 (mission scripts ~9k lines, `Tpp*.lua` libraries); native functions exposed as `Fox.*`, `Tpp*`, `GameObject.*`. `Fox.ExportSerializeInfo()` dumps the entity type DB without patching.
- Quark system table = global subsystem registry keyed by StrCode64. Hashes: StrCode32/64; path hashes CityHash v1.0.x with Fox seeds. Name dictionaries: GzsTool `qar/fpk_dictionary.txt`, FoxTool `fox_dictionary.txt`, `mgsv-lookup-strings`.
- Saves sync with Konami: no save edits, no online testing.

## 2. Community toolchain (versions used here)
| Tool | Role | Version |
|---|---|---|
| Infinite Heaven (TinManTex) | Lua framework, boss events, menus, modules in `mod\modules\` | r267 |
| IHHook | `dinput8.dll` extender, plugins in `plugins\`, Lua pipe (512-byte buffer) | r25 |
| SnakeBite | `.mgsv` installer (Luc installs) | 0.9.2.5 |
| V_Framework (Yazed0071) | native DLL + Lua APIs; installed build is **1.6** (1.7 hangs at title on this install) | 1.6.0.1 |
| GzsTool / FoxTool / FtexTool (Atvaark), FoxEngineTemplates (kapuragu) | archive / DataSet / texture tools, 010 templates | sources in `Research\sources\` |
| Sahelanthropus Boss Events (retali8) | prior free-roam boss mod; re-flags soldier navmesh | r10a |

Patch breakage is the community's main pain: every exe update moves hook addresses (they migrate via Ghidra Version Tracking).

## 3. Sahelanthropus asset chain [D]
| Piece | Identifier |
|---|---|
| GameObject type | `TppSahelan2` + `TppSahelan2Parameter`; locator `TppSahelan2LocatorParameter` (flags 7) |
| DataSets | `/Assets/tpp/level_asset/chara/mecha/sahelan_afgn_1st.fox2` (Hellbound), `sahelan_afgn.fox2` (Dominion) |
| Common pack | `/Assets/tpp/pack/mission2/common/mis_com_sahelan.fpk` |
| Ep31 extras (required!) | `s10151_special_npc.fpk(d)`: 25 files — `.gskl`/`.fcnp` for `miss0-2`, `msbl0`, `srcm0`, `grnd0`, their `.parts`/`.tgt`, rock models, fova `mgs0_cv.fox2`, `mgs_cv_pwup.fv2` |
| Model / rig | `mgs0_main0_def.fmdl`, `tpp_sahelan_all.frig`, `.frdv`, `.gskl`, `.fcnp` |
| Hitboxes | `/Assets/tpp/parts/mecha/mgs/SahelanTargetDefense*.tgt` |
| Animation | `TppSahelan2_layers.mog/.mtar` (Dominion), `TppSahelan2for1st_layers.*` (Hellbound); player extras `pl_mission_s10151.mtar` |
| Sound / VFX | `se_e_mgs.sdf`; ~50 `.vfx` |
| Attacks | 16 `ATK_Sahelan_*` (FootStamp, RodAttack, HeadVulcan, ParasiteSword, Small/MidleMissile, AirMine, Grenade, Flame, RailGun, PileBunker, Stomp, RockExplosion, TowerBreak …) |
| Messages | 33, e.g. `SahelanPartsBroken`, `SahelanHeadBroken`, `SahelanChangePhase`, `Sahelan1stRailGun`, `SahelanBlastDamageToWeakPoint`; exe phases `SAHELAN2_PHASE_1ST…8TH`, `ALERT`, `CAUTION`, `SNEAK`, `VS_HELI` |

Verified data facts: the only `sahelan`-world navmesh is `s10151_nav_sahelan.nav2` (Ep31 arena) [D]; `Tpp/start.lua` line 152 `AddWorld{worldName="sahelan", maxLoadFileCount=2}` (Lua, changeable) [D]; generation params radius 8 / height 25 / 640 m tiles in `afgh_common_nav.fox2` [D]; `SetRelativeRouteNode` is used in Ep12 (`s10070_enemy03.lua`) [D]; difficulty is scriptable via `SetCombatGrade{defenseValue, defenseValueForWeakPoint, offenseGrade, defenseGrade}` [D]. Leads: `mgs0_ldrf0_def.fmdl` unreferenced, `mgs_cv_pwup.fv2` = likely Extreme paint [I].

## 4. Option A: "Sahelanthropus Unbound" (IH boss type) — history
Built as an IH r267 boss (`InfBossEvent` + `InfBossTppSahelan2.lua` + addon), packaged by `Tools\build_sahelan_unbound.py` (own fpk/fpkd + fox2 + SnakeBite writers, byte-identical round trips on all game packages/DataSets).

- **t1/t1b/t1c** crashed at `mgsvtpp+0xADBFBB` (null bone in a transform lookup). Root cause: missing Ep31 skeletons/parts. **t1d** added the 25 `s10151_special_npc` files → full fight works (2026-10-14).
- **t1e:** difficulty presets (Normal 35k life, Extreme 55k + Ep50 combat grade), heli attacks, search-missile routes, red fog at phase 8+; `ReportStatus()` to fit the 512-byte pipe.
- Death-reload hang: `TppSahelan2_block` never reached EMPTIED. **Fixed 2026-10-17** by load mode **MISSION_PACK** (packs load with free roam, no script block).
- **t2a/t2b:** Africa sub type at Nova Braga Airport (`sahelan_mgs0_dominion_mafr`), mission filter per sub type, `InfControlSally.lua` menu. Current build `Mods\_build\Sahelanthropus Unbound t2b.mgsv`.
- Never done: A4 raise `maxLoadFileCount`, A5/A6 generate a mech-sized navmesh (superseded by Option B's `navPatch` + DirectPath).

## 5. Planned next RE milestone (from the FoxRe agent, unverified [?])
Milestone 4 = FoxLua C API / script bridge: `SetLuaFunctions` 0x1408D81F0 and `FoxLuaRegisterLibrary` 0x14006B8C0, lua_* API addresses 0x141A114D0–0x141A12300, Fox userdata types (Vector3/Quat/Matrix4), the 264 native bindings in `lua_bindings.tsv`. Verify every address before use (that agent had several wrong claims; see `mgsv_unified_server\docs\FOXRE_REVIEW.md`).

---
<small>Source: `docs/BACKGROUND.md` in the project repository &middot; generated 2026-10-23.</small>
