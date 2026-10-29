# Run your own Lua from a package

*Based on: [How a mission loads](../explain/mission-load.md), [The Lua script host](../explain/script-host.md). Exact details: [Resources and mission load](../engine/resources.md), [Script host](../engine/script-host.md).*

## The finding
Every `.lua` entry of a loaded package is a **script resource** that runs when the package loads [V]. Within one package they run in reverse of the stored entry order, which in every game package equals alphabetical path order [V]. A table the script returns becomes a global named after the file (`mymod_main.lua` returns `{...}` → global `mymod_main`) [V]. A script that another loaded package already holds is not run again; when its last package unloads, it is gone and runs anew next time [V].

## How it works
- The order across packages follows the package list; within a package, path order decides.
- `mission_main.lua` runs once per mission load; your script does too if it lives in a mission package.
- Packaged scripts may be obfuscated (`0x1B` / `0x1C` header bytes); plain-text Lua is accepted as is.

## How this would be used in a mod
*Hypothetical example.* A mod ships `/Assets/mymod/script/mymod_main.lua` inside its own `mymod.fpkd`, added to free roam as in [Add a package to a mission](add-a-package.md):

```lua
-- /Assets/mymod/script/mymod_main.lua
local this = {}
function this.OnMissionCanStart()
  -- runs when called from the mission; safe to use mvars here
end
return this                   -- becomes the global `mymod_main`
```
Another script of the same mission can then call `mymod_main.OnMissionCanStart()`. If the mod needs two files in a fixed order, name them so their paths sort in that order (`a_defs.lua` before `b_logic.lua`), since that is the run order.

## Pitfalls
- `mvars` is replaced with a fresh table whenever a mission object is created or destroyed [V]: keep long-lived state elsewhere.
- `print` and `Fox.Log` do nothing in the release build [V]; log through your own file output.
- Test offline: the project's script host runs the game's own boot and mission load without the game, with a package-scoped file system that hides a script until its package is mounted, so "works by accident" bugs show up.

---
<small>Hand-written article (`docs/site/mods/Lua-From-Packages.md`) &middot; published 2026-10-29.</small>
