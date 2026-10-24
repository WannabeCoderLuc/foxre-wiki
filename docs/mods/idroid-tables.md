# Patching the iDroid tables

*Based on: [The iDroid and the language reload](../explain/idroid.md) (M5). Exact details: [Resources and mission load, "UI parameter tables"](../engine/resources.md).*

## The finding
The iDroid's map and pause-help tables (`mbdvc_map_location_parameter.lua`, `mbdvc_map_mbstage_parameter.lua`, `mbdvc_map_mission_parameter.lua`, `mbdvc_pause_help_table.lua`) are the scripts of `/Assets/tpp/pack/mbdvc/mb_dvc_top.fpk` [V]. Every `TppUiCommand.ChangeLanguage()` reloads that package and runs the four scripts again, even when the language does not change [V live]. A normal start-up does it three times: during the boot, after reading the config save, and while loading the save data [V live]. `IsChangeLanguage()` is true until the reload is finished [V].

## How it works
`ChangeLanguage` sets a "change pending" flag; the iDroid's update steps through a reload (fonts and texts for the language, then `mb_dvc_top`) and clears the flag. Each reload re-creates the globals the tables define.

## How this would be used in a mod
*Hypothetical example.* A mod adds landing zones to the map table (Infinite Heaven builds ground start positions from these tables, for instance). Two ways that survive reloads:

1. **Ship a modified `mb_dvc_top.fpk`** (or a patched copy of the table file inside it): the change is part of the package and is re-applied on every reload automatically.
2. **Re-apply after each reload**: watch `TppUiCommand.IsChangeLanguage()` turn from true to false and patch the globals again:

```lua
local wasChanging = false
function this.Update()
  local changing = TppUiCommand.IsChangeLanguage()
  if wasChanging and not changing then
    this.AddMyLandingZones(mbdvc_map_location_parameter)   -- tables were just re-created
  end
  wasChanging = changing
end
```
Calling `TppUiCommand.ChangeLanguage()` yourself is a way to force a reload, for example after editing the table files during development.

## Pitfalls
- Patching the globals once at start-up is lost at the next reload; the start-up itself reloads them twice after the boot.
- A script error in a table file breaks the iDroid map after every reload; test the file offline.

---
<small>Hand-written article (`docs/site/mods/IDroid-Tables.md`) &middot; published 2026-10-24.</small>
