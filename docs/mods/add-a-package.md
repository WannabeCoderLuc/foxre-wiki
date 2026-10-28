# Add a package to a mission

*Based on: [How a mission loads](../explain/mission-load.md) (M5, PASS). Exact details: [Resources and mission load](../engine/resources.md).*

## The finding
The executable never decides which packages a mission loads. It asks Lua: `Mission.SetMissionPackagePathFunc` registers `TppMissionList.GetMissionPackagePath`, and the engine calls it with the mission code and loads whatever list comes back [V]. Each mission's list is built by a function in `TppMissionList` using `TppPackList` helpers, for example free roam f30010:

```lua
-- vanilla TppMissionList (shape of the f30010 entry)
s[30010] = function(p)
  TppPackList.AddLocationCommonScriptPack(p)
  TppPackList.AddLocationCommonMissionAreaPack(p)
  TppPackList.AddMissionPack(TppDefine.MISSION_COMMON_PACK.ORDER_BOX)
  -- ...
end
```
`TppPackList.AddMissionPack(path)` only appends a string to the list being built [V].

## How it works
1. Lua calls `Mission.LoadMission()`; on a later frame the engine calls the package-path function.
2. The packages load in list order once the location is ready; every `.lua` inside them runs at once.
3. The two vehicle-colouring packages are appended by the engine itself (every mission except 30050).

## How this would be used in a mod
*Hypothetical example.* A mod wants an extra prop pack and a script in Afghanistan free roam. `TppMissionList.lua` ends with `Mission.SetMissionPackagePathFunc(a.GetMissionPackagePath)`; the engine keeps a reference to *that function object* [V], so replacing the Lua field later is not enough. The mod registers its own wrapper:

```lua
local vanilla = TppMissionList.GetMissionPackagePath
local function withMyPack(missionCode)
  local list = vanilla(missionCode)            -- a table of paths (or nil)
  if missionCode == 30010 and type(list) == "table" then
    table.insert(list, "/Assets/mymod/pack/mymod_props.fpk")
  end
  return list
end
Mission.SetMissionPackagePathFunc(withMyPack)
```
Nothing in the executable changes; the new package is loaded by the same code path as Konami's own, at the same moment, and its scripts run on load.

## Pitfalls
- The list function runs under `pcall`; if it errors, the engine loads **nothing** for that mission. Test it offline first.
- The location must already be loaded; a package that depends on another location's assets will fail quietly.
- Register the wrapper after `TppMissionList` has run and before the mission load you want to change; the location function (`SetLocationPackagePathFunc`) works the same way.

---
<small>Hand-written article (`docs/site/mods/Add-A-Package.md`) &middot; published 2026-10-28.</small>
