# World streaming and locators

Clean-room spec for `Engine\world\` (roadmap M6). Tags: [V] read in the exe / matched against live data, [D] read in game data, [I] inferred, [?] open.
Started 2026-10-29. Static reading of `GameBackup\MGS_TPP\mgsvtpp.exe`; live reference `Engine\tests\fixtures\m6_block_messages.json` (`Tools\m6_block_fixture.py`) from the luaret captures `trace_m5_luaret_20261023_115514` (title 40010 → f30010, afgh save) and `trace_m4b_luaret_f30020_20261029_002259` (title 40020 → f30020, mafr save), 2 runs each. Verifier: `Engine\tests\test_m6_world.py`.

## Status
| Part | State |
|---|---|
| DataIdentifier registry + `GetDataWithIdentifier` / `GetDataBodyWithIdentifier` | decoded [V static], implemented (`Engine\world\identifiers.py`), matches live lookups for both saves |
| Locator world transform (`Tpp.GetLocatorByTransform`) | implemented; formula [V live] from the M2 gate (17/17 f30010 checkpoint locators) |
| FSTB large-block table | records decoded incl. small-block lists (`Engine\world\stage_blocks.py`); LOD package lists [?] |
| Stage-block controller (small-block index, large-block state, messages) | decoded [V static], implemented (`StageBlocks`); the host raises the same 4 stage-block messages as live for both saves |
| Title menu → CONTINUE through the game's own flow | open: the title now reaches `active`; the CONTINUE hand-drive in `scenario.py` stays until the title-menu UI messages are delivered |

## DataIdentifier lookup [V static]
- **Registry:** one global multimap of DataIdentifier entities (0x142B72A88, lock 0x142B72A98), keyed by the code of the `identifier` string (`fox::Path` built from the string). The DataIdentifier constructor (0x14017E9E0, vtable 0x1420E97E0) inserts the new entity (0x14017ECC0), the destructor (0x14017EB20) removes it (0x14017F600), the `identifier` property setter (0x14017F2F0) removes and re-inserts it. An identifier is therefore visible exactly while the DataSet holding it is loaded.
- **Lookup** (0x14017EDD0, `identifier`, `key`): over the equal range of `identifier` (registration order), look `key` up in each DataIdentifier's `links` table — a hash table with `2 × n` buckets (n at +0x84, bucket heads u32 at +0x98, 0x18-byte entries at +0xA0 with the key-string object at +0 and the next index at +0x10, values 0x28 bytes at +0xA8); keys compare on the 48 low bits of StrCode64(key). First hit: the linked Data (value handle → +0x18). No hit in any: NULL.
- **Lua:** `DataIdentifier.GetDataWithIdentifier(identifier, key)` (0x14017F170) returns that Data or NULL; `GetDataBodyWithIdentifier` (0x14017F030) returns the Data's body (Data +0x68), or a null body.
- **Script use** (vanilla `Tpp.lua`): `Tpp.GetDataWithIdentifier(id, key, cls)` = lookup + `IsKindOf(cls)`; `Tpp.GetLocatorByTransform(id, key)` = `GetDataWithIdentifier(id, key, "TransformData").worldTransform` → `translation`, `rotQuat`.
- **World transform** [V live, M2 gate]: local transform (`transform` entity: translation, rotation, scale) composed up the `parent` chain: `p_world = parent_rot · (parent_scale ∘ p_local) + parent_world_pos`, `q_world = parent_world_rot · q_local`.

Engine model (`Engine\world\identifiers.py`): the registry is derived from the DataSets of the currently mounted packages (a package's DataSets live as long as the package), registration order = mount order then entity order [I: the game registers in DataSet creation order]; Data objects reach Lua as proxy tables with `name`, `worldTransform`, `transform`, `IsKindOf`.

Live check: the title heli space asks `HelispaceLocatorIdentifier` for `BuddyQuietLocator` then `BuddyDDogLocator` (from `heli_common_sequence` buddy setup), both answered with a Data, in both saves (afgh f1932, mafr f1616); the host makes the same two lookups in the same order with the same outcome, and 40010 / 40020 finish `OnAllocate` + `OnInitialize` with no Lua error (`test_m6_world.py`). The identifier lives in `h40010_sequence.fox2` / `h40050_sequence.fox2` [D].

## Stage blocks — live messages [V live]
Both runs of each capture log the same 8 Block messages:

| # | Message | afgh save (f30010) | mafr save (f30020) |
|---|---|---|---|
| 1–2 | `StageBlockCurrentSmallBlockIndexUpdated(x, y)` | (7945, 7945), (57857, 57857) | same |
| 3 | `StageBlockCurrentSmallBlockIndexUpdated(x, y)` | (128, 125) | (140, 144) |
| 4 | `OnChangeLargeBlockState(name, ACTIVE)` | `afgh_powerPlant` | `mafr_pfCamp` |
| 5–8 | `OnScriptBlockStateTransition(name, state)` | quest_block 0, reinforce_block 0, animal_block 0, animal_block 1 | quest_block 0, quest_block 1, animal_block 0, animal_block 1 |

- Large-block `name` = StrCode32 of the large package's file stem (`pack_large/<name>.fpk`) [V].
- Messages 1–2 are the controller's two sentinel positions ("Stage-block controller" below): 7945 = +1,000,000 (constructor), 57857 = −1,000,000 (`DisablePosition` in the title heli space) [V].
- mafr: block (140, 144) lies in `mafr_pfCamp`'s box [V]. afgh: (128, 125) is two rows outside `afgh_powerPlant`'s box, but the 5×5 window widened by `largeBlockLoadingMargin` reaches its small-block list (activation rule below) [V].

## FSTB large-block table [D]
Header beyond the common-package part (Resources.md "FSTB"): +0x08 u32 2 (sections), +0x0C u32 0x18 (section table), +0x18 u32 offset of the large-block section, +0x1C u32 its end; section: u32 n (afgh 15, mafr 11), u32[n] record offsets.
Record: +0x00 StrCode32(name) [V live], +0x04 u32 1 in every record [?], +0x08 kind (0: no LOD packages, 2: LOD packages) [D], +0x0C string offset of the superlow LOD model (afgh) or "" (mafr), +0x10 number of LOD packages (2 / 0 with the kind) and +0x14 offset of their list [D; list layout ?], **+0x18 offset of the small-block list, +0x1C its length: u32 entries `x | y << 16`** [V: the controller reads them as u16 (x, y) pairs; every entry lies in the box; the list ends at the next record], +0x20 / +0x24 box min / max `x | y << 16` (inclusive) [V live], +0x28 string offset of the large package path. At runtime: groups of 0x38-byte entries, name at +0x28 (0x14015F4F0) [V static]; group assignment [?] (host: one group; live `GetLoadedLargeBlocks(0)` returns pfCamp).

## Stage-block controller [V static unless tagged]
Per-frame update 0x1401611F0 → 0x140161500; parameters copied from `StageBlockControllerData` (0x140165BD0). afgh and mafr: blockSize 128, count 5×5, centerIndex 133, blockMargin 3, largeBlockLoadingMargin 1 [D].

- **Position:** one global provider `StageBlockCurrentPositionSetter` (0x142B729A8: enable +0x14, x / y / z ints +0x18..+0x20). `SetPosition(x, z)` or `(x, y, z)` (0x1401779F0, `lua_tointeger`), `SetEnable` (0x1401779C0), `DisablePosition` (0x14015F110: all axes −1,000,000). The controller reads the first enabled provider's (x, z) (0x14015F370); none enabled → the last position stays. Constructor position +1,000,000 (0x14015CEAB).
- **Who sets it:** `TppMain.StageBlockCurrentPosition`: `SetPosition(vars.initialPlayerPosX, vars.initialPlayerPosZ)` when `vars.initialPlayerFlag == PlayerFlag.USE_VARS_FOR_INITIAL_POS` (1); heli spaces: `DisablePosition`, then wait for `LargeAndSmallBlocksAreEmpty`; `OnTextureLoadingWaitStart` disables the provider outside heli spaces [D Lua]. On CONTINUE the vars come from the CHECK_POINT slot (saved from `vars.playerPos*` by `TppPlayer.SetInitialPositionToCurrentPosition`), not from `gvars.ply_missionStartPos` [V live: f30020 vars = slot = (1006.16, 1418.84); f30010 SetPosition args (−629.90, −913.37), trace_m5_luaret].
- **Minimum small-block index** per axis: `trunc((center·size + size/2 + p − count·size/2 − origin) / size)` (C division, 16-bit); the window centre cell is `center + floor(p / size)`; origin (controller +0x7C) = 0 [V: fits both sentinels and both saves]. Kept while p stays within the old centre cell widened by blockMargin (controller +0x158 [I: param copy offset]). `StageBlock.GetCurrentMinimumSmallBlockIndex` returns it (+0x324, 0x140177F10).
- **Index message:** `Block.StageBlockCurrentSmallBlockIndexUpdated(min + count/2)` (tags 9: two ints) when the index differs from the last reported one (+0x334); only the location's global controller (0x142B70F40) raises it (0x140161816).
- **Large blocks:** when the index changes with a valid position (x ≠ +1e6), for each FSTB large block: list A = one of its small blocks lies in the count × count window from the minimum index; list B = the same window widened by `largeBlockLoadingMargin` (controller +0x168 = param +0x70 ← data 0x108) on each side (0x140161500). Each list fills its own slot set (A: `largeBlockCount*` slots, B: +0x2B0 slots); slots of blocks no longer wanted unload. Engine model: a block is loaded while it is in B (A ⊂ B) [I: which slot set drives the message]; afgh `powerPlant` is only in B, mafr `pfCamp` in both, one message each [V live].
- **Large-block message:** listener vtable 0x1420E7C00 slot 5 (0x140177870): `Block.OnChangeLargeBlockState(name, state)`, ACTIVE (1) for slot state 3, INACTIVE (0) for 2, only for names registered with `StageBlock.AddLargeBlockNameForMessage` (0x140177BD0, ≤ 18 names; `afgh_base` / `mafr_base.baseList`), tags 10. `OnChangeSmallBlockState` (0x140177AC0, slot 4) is the small-block counterpart (`AddSmallBlockIndexForMessage`) [V static; not modelled].
- **Order:** the controller exists with the location; its first update (ctor position → message 1) runs before the title's `DisablePosition` (message 2); free roam: SetPosition → index message → large block loaded → ACTIVE after the base list is registered [V live order]. Host: first update from the location package hook, large-block load = one update (`LOAD_FRAMES`) [I].

Engine model (`Engine\world\stage_blocks.py`): `PositionSetter`, `StageBlockController` (index, hysteresis, list-B large blocks, messages), `StageBlocks` (host: controller per location `StageBlockControllerData`, `StageBlock` / `StageBlockCurrentPositionSetter` Lua libraries). Save images carry `vars.initialPlayerFlag / PosX / PosZ`. Verifier: `test_m6_world.py` (`test_small_block_index_formula`, `test_host_stage_block_messages_match_live`: host = live for f30010 and f30020).

## Open
- Stage blocks: which slot set (A window / B margin) drives `OnChangeLargeBlockState`; FSTB record +0x04 and the LOD package lists; small-block / LOD streaming (`OnChangeSmallBlockState`) not modelled; real load latency of a large block.
- Title-menu messages (`TitleMenuReady`, `EndFadeIn`, `TitleMenu`) and the game's own CONTINUE (E13).

## Evidence
| VA | What | Tag |
|---|---|---|
| 0x14017F170 | `DataIdentifier.GetDataWithIdentifier` | V static |
| 0x14017F030 | `DataIdentifier.GetDataBodyWithIdentifier` (Data +0x68) | V static |
| 0x14017EDD0 | registry lookup: equal range + links hash table | V static |
| 0x14017E9E0 / 0x14017EB20 / 0x14017F2F0 | DataIdentifier ctor (register), dtor (unregister), `identifier` setter (re-key) | V static |
| 0x14017ECC0 / 0x14017F600 | registry insert / remove (multimap 0x142B72A88) | V static |
| 0x1401611F0 / 0x140161500 | controller update: position → minimum index, hysteresis, large-block lists A / B, index message (raise 0x140161816) | V static |
| 0x140177870 / 0x140177AC0 | listener vt 0x1420E7C00 slots 5 / 4: OnChangeLargeBlockState / OnChangeSmallBlockState raisers, name filter | V static |
| 0x14015F370 / 0x14015F110 / 0x1401779F0 | position provider read / DisablePosition (−1e6) / Lua SetPosition | V static |
| 0x14015CEAB, 0x1429E4858 / 0x1429E485C | ctor position +1,000,000; sentinels ±1,000,000 | V static |
| 0x140165BD0 | StageBlockControllerData → controller parameters (blockMargin, loadingDistance, largeBlockLoadingMargin …) | V static |
| 0x14015F4F0, 0x14015B900 / 0x14015B940 | large-block name by (group, index); entry / group counts (0x38-byte entries) | V static |
| m6_block_messages.json | live Block.* messages + lookups, 2 saves × 2 runs | V live |
| Memory/research/m6_initialpos_20261029_132101 | f30020 vars.initialPlayerPos = CHECK_POINT slot, minimum index (138, 142) | V live |

---
<small>Source: `docs/engine/World.md` in the project repository &middot; generated 2026-10-29.</small>
