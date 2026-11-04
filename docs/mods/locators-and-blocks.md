# Locators and map blocks in a mod

*Based on: [World streaming and the title screen](../explain/world-streaming.md) (M6, PASS). Exact details: [World streaming and locators](../engine/world.md), [Resources and mission load](../engine/resources.md). Addresses are for 1.0.15.4 EN.*

## The findings
- **Named places are DataIdentifiers.** A `DataIdentifier` entity in a DataSet holds a table of keys, each linked to an entity. `DataIdentifier.GetDataWithIdentifier(identifier, key)` returns that entity, or nil [V]. An identifier exists **exactly while the DataSet that holds it is loaded** [V].
- If two loaded DataSets use the same identifier name, the lookup tries them in registration order and returns the first hit [V].
- `Tpp.GetLocatorByTransform(identifier, key)` returns the world `translation` and `rotQuat` of a locator: its local transform composed up its parent chain [V live, 17 of 17 objects].
- **The map loads in 128 m blocks** around one position. The window is 5 × 5 blocks; block indices are counted from centre index 133, so the window's centre block is `133 + floor(p / 128)` on each axis [V, both free-roam maps].
- The position comes from `StageBlockCurrentPositionSetter`. On a mission start or continue, `TppMain` sets it from `vars.initialPlayerPosX / Z`; heli spaces call `DisablePosition` [V].
- The window only moves when the player leaves the current centre block plus a margin of 3 blocks (hysteresis) [V].
- **Large blocks** (bases and other big areas, e.g. `afgh_powerPlant`, `mafr_pfCamp`) load when one of their small blocks lies in the window widened by one block (`largeBlockLoadingMargin` 1) [V]. Afghanistan has 15, Africa 11 [D].
- Scripts hear about it through **`Block` messages**: `StageBlockCurrentSmallBlockIndexUpdated(x, y)` when the window moves, and `OnChangeLargeBlockState(name, state)` (ACTIVE 1, INACTIVE 0) **only for names registered with `StageBlock.AddLargeBlockNameForMessage`** (at most 18) [V].

## Looking up a named place
```lua
-- vanilla pattern (Tpp.lua): position and rotation of a locator
local pos, rot = Tpp.GetLocatorByTransform("HelispaceLocatorIdentifier", "BuddyQuietLocator")
```
`Tpp.GetLocator(identifier, key)` returns the position as a table and the rotation as a Y angle in degrees [vanilla Lua]. Vanilla quests ship their own identifiers this way, for example `identifier_q80020_esc_pos` with keys `start`, `crevice`, `rock` in quest q80020 [vanilla Lua], so a mod's own DataSet with its own identifier follows an existing pattern.

`Tpp.GetDataWithIdentifier(id, key, className)` does the same lookup and also checks the entity's class with `IsKindOf` [V].

Because identifiers come and go with DataSets, a lookup works only while the package holding the DataSet is loaded. A lookup in a mission script for an identifier in a large block's package fails while that block is not loaded.

## Knowing when an area is loaded
Large-block messages are filtered: the game only sends them for names a script registered. Vanilla registers its base lists (`afgh_base`, `mafr_base.baseList`) [V]. The sequence, as seen live in free roam [V]:

1. Position set → `StageBlockCurrentSmallBlockIndexUpdated(x, y)`.
2. The large block's package loads.
3. `OnChangeLargeBlockState(StrCode32(name), ACTIVE)`, if the name was registered.

The `name` argument is the StrCode32 of the large package's file stem (`pack_large/<name>.fpk`) [V].

## How this would be used in a mod
*Hypothetical example; not built or tested.* A mod places extra guards when the player gets near a base, using a locator it ships in its own DataSet inside that base's package.

```lua
-- 1. ask for the message (vanilla registers its own bases the same way)
StageBlock.AddLargeBlockNameForMessage({ "afgh_powerPlant" })   -- vanilla passes a list of names

-- 2. react in the mission's Messages table
Block = {
  { msg = "OnChangeLargeBlockState",
    func = function(name, state)
      if name == Fox.StrCode32("afgh_powerPlant") and state == 1 then   -- ACTIVE
        local pos, rot = Tpp.GetLocatorByTransform("MyModPowerPlantIdentifier", "GuardSpot01")
        if pos then
          -- spawn or move your guard here
        end
      end
    end },
},
```
What it relies on: the message fires only for registered names [V]; the identifier is visible once its DataSet is loaded [V]. Vanilla's `afgh_base.OnInitialize` already registers its whole base list with one call [vanilla Lua]; whether a second call adds to that list or replaces it is not decoded [?], so a real mod must check this first, and the 18-name limit applies [V].

## Pitfalls
- **The 18-name limit** for large-block messages is shared with vanilla's own base list.
- **Hysteresis**: the window does not follow the player block by block; it waits until the player is 3 blocks past the centre block. Do not expect an index message every 128 m.
- **Two sentinel positions** (+1,000,000 at creation, −1,000,000 after `DisablePosition`) produce index messages too: 7945 and 57857 on both axes [V]. Ignore them.
- Which of the two window lists (the 5 × 5 window or the widened one) drives the large-block message is not decoded [I: the widened one in our model]. Real load time of a large block is not measured.
- Small-block messages (`OnChangeSmallBlockState`) exist but are not modelled by the project [V static only].
- On CONTINUE the position comes from the checkpoint save (`vars.initialPlayerPos*`), not from `gvars` mission start values [V live].

---
<small>Hand-written article (`docs/site/mods/Locators-And-Blocks.md`) &middot; published 2026-11-05.</small>
