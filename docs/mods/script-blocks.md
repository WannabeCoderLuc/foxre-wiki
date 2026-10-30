# Side content with script blocks

*Based on: [Script blocks](../explain/script-blocks.md). Exact details: [Resources and mission load, "Script blocks"](../engine/resources.md).*

## The finding
8 global slots load packages with their own script, independently of the mission [V]. A slot exists while a `ScriptBlockData` entity of a loaded DataSet exists [V]. `ScriptBlock.Load(id, packages)` requests a load; the block script gets `OnAllocate` (coroutine), `OnInitialize`, `OnUpdate` every frame while loaded, and `OnTerminate` before it unloads [V]. `GetScriptBlockState` reports EMPTY 0, PROCESSING 1, INACTIVE 2, ACTIVE 3; `Activate` / `Deactivate` switch a loaded block [V]. Quest and animal blocks survive a save in `svars.sbl_*` [V].

## How it works
- A new `Load` with a different package list unloads the current one first (calling its `OnTerminate`), waits a few frames, then loads.
- The engine picks the block's script as the first script resource in its packages that returns a table.
- `TppScriptBlock` (Lua) keeps named pack lists per block (`RegisterCommonBlockPackList`) and saves what is loaded.

## How this would be used in a mod
*Hypothetical example.* A mod adds a roaming event near one outpost and wants it in memory only while the player is close. It ships `myevent.fpk` (assets plus `myevent_block.lua` returning a table with the four callbacks) and reuses a slot the mission already has, such as the quest block when no quest is active:

```lua
local id = ScriptBlock.GetScriptBlockId("quest_block")
if ScriptBlock.GetScriptBlockState(id) == ScriptBlock.SCRIPT_BLOCK_STATE_EMPTY then
  ScriptBlock.Load(id, "/Assets/mymod/pack/myevent.fpk")
end
-- later, when the player leaves the area:
ScriptBlock.Load(id, nil)        -- unload: OnTerminate runs, then the slot empties
```
`myevent_block.lua` spawns its content in `OnInitialize`, runs its logic in `OnUpdate` and cleans up in `OnTerminate`.

## Pitfalls
- Slots belong to the mission's DataSets: they disappear with the mission. Do not cache an id across missions.
- Sharing a slot with vanilla content (quests) means you must give it back; a mod that adds its own `ScriptBlockData` to its mission package gets its own slot (up to 8 in total).
- `svars.sbl_*` restore the vanilla quest/animal blocks on Continue; your block is not saved unless you save its state yourself.

---
<small>Hand-written article (`docs/site/mods/Script-Blocks.md`) &middot; published 2026-10-30.</small>
