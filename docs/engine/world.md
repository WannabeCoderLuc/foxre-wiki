# World streaming and locators

Clean-room spec for `Engine\world\` (roadmap M6). Tags: [V] read in the exe / matched against live data, [D] read in game data, [I] inferred, [?] open.
Started 2026-10-29. Static reading of `GameBackup\MGS_TPP\mgsvtpp.exe`; live reference `Engine\tests\fixtures\m6_block_messages.json` (`Tools\m6_block_fixture.py`) from the luaret captures `trace_m5_luaret_20261023_115514` (title 40010 → f30010, afgh save) and `trace_m4b_luaret_f30020_20261029_002259` (title 40020 → f30020, mafr save), 2 runs each. Verifier: `Engine\tests\test_m6_world.py`.

## Status
| Part | State |
|---|---|
| DataIdentifier registry + `GetDataWithIdentifier` / `GetDataBodyWithIdentifier` | decoded [V static], implemented (`Engine\world\identifiers.py`), matches live lookups for both saves |
| Locator world transform (`Tpp.GetLocatorByTransform`) | implemented; formula [V live] from the M2 gate (17/17 f30010 checkpoint locators) |
| FSTB large-block table | prefix decoded (`Engine\world\stage_blocks.py`); small-block lists, LOD tables, load-region bitmask [?] |
| Stage-block controller (small-block index, large-block state, messages) | live messages captured; controller not decoded or implemented [?] |
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
- Messages 1–2 come before the free-roam location is loaded; 7945 = 0x1F09 and 57857 = 0xE201 look like sentinel / uninitialised indices [?].
- mafr: block (140, 144) lies in `mafr_pfCamp`'s box (x 138–143, y 139–144) [V]. afgh: `afgh_powerPlant` turns ACTIVE with the player at (128, 125), two rows outside its box (x 126–129, y 118–123): activation uses a load range or the load-region bitmask, not the box [?].

## FSTB large-block table [D]
Header beyond the common-package part (Resources.md "FSTB"): +0x08 u32 2 (sections), +0x0C u32 0x18 (section table), +0x18 u32 offset of the large-block section, +0x1C u32 its end; section: u32 n (afgh 15, mafr 11), u32[n] record offsets.
Record prefix: +0x00 StrCode32(name), +0x04 u32 1 [?], +0x08 kind (0: inline small-block list; 2: LOD packages + load-region bitmask) [D], +0x0C string offset of the superlow LOD model (afgh) or "" (mafr), +0x1C number of small blocks, +0x20 / +0x24 box min / max as `x | y << 16` (inclusive) [V live for x/y order], +0x28 string offset of the large package path. Remaining fields (LOD package lists, bitmask origin/size, block lists) [?].

## Open
- Stage-block controller: who computes the small-block index from the player position (block size, origin), the large-block activation rule (load range / bitmask), the message raise sites and their order against the location loader (E20, E21). Start: `StageBlockControllerData` (fox_edb), `StageBlock` Lua library (0x140177BD0–0x140178060), `Block` message raisers.
- Messages 1–2 (sentinel indices) [?].
- Title-menu messages (`TitleMenuReady`, `EndFadeIn`, `TitleMenu`) and the game's own CONTINUE (E13).

## Evidence
| VA | What | Tag |
|---|---|---|
| 0x14017F170 | `DataIdentifier.GetDataWithIdentifier` | V static |
| 0x14017F030 | `DataIdentifier.GetDataBodyWithIdentifier` (Data +0x68) | V static |
| 0x14017EDD0 | registry lookup: equal range + links hash table | V static |
| 0x14017E9E0 / 0x14017EB20 / 0x14017F2F0 | DataIdentifier ctor (register), dtor (unregister), `identifier` setter (re-key) | V static |
| 0x14017ECC0 / 0x14017F600 | registry insert / remove (multimap 0x142B72A88) | V static |
| m6_block_messages.json | live Block.* messages + lookups, 2 saves × 2 runs | V live |

---
<small>Source: `docs/engine/World.md` in the project repository &middot; generated 2026-10-29.</small>
