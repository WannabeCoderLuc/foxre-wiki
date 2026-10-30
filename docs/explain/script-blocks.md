# Script blocks

*Milestone M5. Reference: [Resources and mission load, "Script blocks"](../engine/resources.md).*

## What it is
A mission package is loaded once and stays. Side content (a quest, a reinforcement helicopter, the animals of the current area) comes and goes while you play. For that the engine has **8 global script-block slots**: each slot can hold its own packages and its own script, load and unload independently, and be active or inactive.

## Why it matters
Script blocks are how the game keeps memory free in a large open world: only the quest near you, only the animals of your area. They are also the natural home for mod content that should appear and disappear with the player's position.

## How the original does it
- **Slots come from data.** A slot exists while a `ScriptBlockData` entity of a loaded DataSet exists. In free roam f30010 the mission's own DataSets create four: `reinforce_block` (slot 0), `orderBoxBlock` (1), `animal_block` (2), `quest_block` (3), in creation order.
- **Lua drives them** with `ScriptBlock.Load(id, packages)`, `Activate`, `Deactivate`, `Reload`, and reads `GetScriptBlockState(id)`: EMPTY 0, PROCESSING 1, INACTIVE 2 (loaded), ACTIVE 3.
- **Each frame** a slot with a request unloads what it holds (calling the old script's `OnTerminate`), waits a few frames, then loads the new packages. When they are loaded the engine finds the first script in them that returns a table and runs its `OnAllocate` (a coroutine), then `OnInitialize`, then `OnUpdate` every frame while loaded.
- **State changes are announced** with the message `OnScriptBlockStateTransition` (LOADED, ACTIVATED, DEACTIVATED, EMPTIED).
- **Saves remember them.** The quest and animal blocks are saved in `svars.sbl_*`; on Continue, `TppScriptBlock.ReloadScriptBlock` loads them again.

In the live boot three blocks load after Continue: the saved quest (`quest_q52015.fpk`), its reinforcement helicopter (from the quest's own `OnAllocate`), and the animals of the current small block (`powerPlant_SE`), which waits until the mission may start.

## How the new engine does it
`Engine/resources/blocks.py` (`ScriptBlocks`) implements the slots, the natives, the per-frame state machine and the four script callbacks; a smaller `CommonMotionBlock` covers the soldiers' shared motion package.

## How we know it is right
The gate test checks the slot order, the three `ScriptBlock.Load` calls and their packages, the final states (reinforce loaded, animal active, quest loaded) and the chunk order, all against two live captures and a Lua trace of the real game.

## Still open
Who calls the slot update each frame relative to the mission controller, and how the transition message is delivered (the engine logs it; there is no message delivery to scripts yet).

---
<small>Hand-written article (`docs/site/explain/Script-Blocks.md`) &middot; published 2026-10-30.</small>
