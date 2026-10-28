# Test fixtures

Ground truth the engine tests (`Engine/tests/`) compare against. Each comes from the running game or the executable, never from our own code. Contents stay in the project repository (no game data); this list is generated at every sync.

| Fixture | Size | What it holds |
|---|---|---|
| `f30010_identifiers.json` | 5 KB | M2: names, classes and world positions of 17 objects asked from the running game. |
| `m3_frame_trace.json` | 18 KB | M3: updater-vector changes and the 43 bus messages from boot to free roam (2 identical boots). |
| `m4_lua_bindings.json` | 344 KB | M4: binding map, 399 libraries / 5,532 natives with addresses, kinds, enum values, boot points. |
| `m4_lua_boot.json` | 19 KB | M4/M5: the 170 Lua chunks of a cold boot to free roam, in load order, plus library registrations. |
| `m4_lua_consts.json` | 77 KB | M4: Lua constant tables read statically from the executable. |
| `m4_lua_returns.json` | 944 KB | M4: recorded native return values (FoxTrace luaret captures) used for record/replay. |
| `m5_save_image.json` | 6 KB | M5: the minimal save values behind TppScriptVars.LoadVarsFromSlot (from a live dump). |

---
<small>Generated 2026-10-28 from the project repository.</small>
