# Live captures

Every FoxTrace capture: the game booted with log-only hooks, usually twice, then restored. Raw logs stay in the private workspace; findings go to the Reference pages. Generated list, newest first.

| Date | Capture | Runs | Hooks | Hooked |
|---|---|:-:|:-:|---|
| 2026-10-24 | `oq_callers` | 1 | 7 | `sb_update`, `sb_countdown`, `gom_listener`, `mission_ctl_update`, `timer_start`, `msg_resend_count` and 1 more |
| 2026-10-24 | `m5_lang` | 2 | 10 | `loadbuf`, `emblem_setup`, `emblem_reload`, `mbdvc_top_load`, `lang_reload_sm`, `lang_pack` and 4 more |
| 2026-10-23 | `m5_mbdvc` | 2 | 4 | `mbdvc_top_load`, `ui_tables_slot0`, `emblem_setup`, `loadbuf` |
| 2026-10-23 | `m5_luaret` | 2 | 1014 | `cls`, `bld`, `luaL_loadbuffer`, `ScriptBlock.GetScriptBlockId`, `ScriptBlock.GetCurrentScriptBlockId`, `ScriptBlock.Load` and 1008 more |
| 2026-10-23 | `m4_luaret` | 2 | 2 | `cls`, `bld` |
| 2026-10-23 | `m4_luaret_direct` | 2 | 1024 | `cls`, `bld`, `TppMotherBaseManagement.RegCstDev`, `TppMotherBaseManagement.RegFlwDev`, `TppMotherBaseManagement.RegistWeaponPartsInfo`, `TppMotherBaseManagement.RegisterPoolRewardParam` and 1018 more |
| 2026-10-23 | `m4_luaret_direct` | 1 | 1024 | `cls`, `bld`, `TppMotherBaseManagement.RegCstDev`, `TppMotherBaseManagement.RegFlwDev`, `TppMotherBaseManagement.RegistWeaponPartsInfo`, `TppMotherBaseManagement.RegisterPoolRewardParam` and 1018 more |
| 2026-10-22 | `m4_lua_pcall` | 2 | 3 | `luaL_loadbuffer`, `lua_pcall`, `lua_resume` |
| 2026-10-22 | `m4_lua_boot` | 2 | 5 | `luaL_loadbuffer`, `luaI_openlib`, `luaL_newmetatable`, `lua_pushcclosure`, `lua_setfield` |
| 2026-10-22 | `m4_lua_bindings` | 2 | 5 | `luaL_loadbuffer`, `luaI_openlib`, `luaL_newmetatable`, `lua_pushcclosure`, `lua_setfield` |
| 2026-10-22 | `m4_lua_bindings4` | 2 | 16 | `luaL_loadbuffer`, `luaI_openlib`, `luaL_newmetatable`, `lua_pushcclosure`, `lua_setfield`, `fox_tbl_begin` and 10 more |
| 2026-10-22 | `m4_lua_bindings3` | 2 | 16 | `luaL_loadbuffer`, `luaI_openlib`, `luaL_newmetatable`, `lua_pushcclosure`, `lua_setfield`, `fox_tbl_begin` and 10 more |
| 2026-10-22 | `m4_lua_bindings2` | 2 | 9 | `luaL_loadbuffer`, `luaI_openlib`, `luaL_newmetatable`, `lua_pushcclosure`, `lua_setfield`, `fox_tbl_begin` and 3 more |

---
<small>Generated 2026-10-24 from the project repository.</small>
