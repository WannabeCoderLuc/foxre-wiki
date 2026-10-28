# Entities and DataSet loading

Engine module `Engine\core\entities.py` (`World`) over `Engine\formats\fox2.py` + `Engine\core\typedb.py` · verifier `Engine\tests\test_entities_s10151.py`.
**Static gate (2026-10-21), mission s10151:** 419 mission DataSets + 4 link dependencies (transitive closure, 2 rounds) → **8,669 entities of 140 classes, 100 % typed, 100 % property names resolved, 7,728/7,728 EntityPtr resolved**; every unresolved handle/link falls in a named category below. Load time 3.4 s (Python).
Tags: [V] holds for every reference in the loaded set, [D], [I], [?].

## Model
- `World.add(key, raw, asset_path)` parses a DataSet, types each entity by its class hash (`TypeDB.resolve`), names each property from the class chain, and decodes values: floats from raw bits, String/Path/FilePtr hashes → string-table text, `bool`, StaticArray[1] → scalar, StringMap → dict keyed by resolved names.
- `World.pending_archives()` lists link targets not yet loaded (load them for a dependency closure); `World.resolve()` turns every reference into a `Ref(kind, raw, target, archive, name)`.
- Entity identity = (file, address). `Entity.name` = the `Data.name` property.

## Reference semantics [V on s10151]
| Kind | Encoding | Resolution | s10151 |
|---|---|---|---|
| EntityPtr | u64 address | entity with that address **in the same file**, or 0 = null | 7,728 ok, 0 dangling |
| EntityHandle | u64 address | same file (7,009); else the unique entity with that address in another loaded DataSet (288 — owner/parent links across files, addresses are globally unique per build); else dangling (230: editor-only `GraphxSpatialGraphData*` nodes/edges and transforms whose owner is outside the loaded set) | |
| EntityLink | (packagePath, archivePath, nameInArchive, handle), all StrCode64 except handle | archivePath = target DataSet path (string in the string table, or only its StrCode64); **StrCode64("") = 0xB8A0BF169F98 means "this file"**; target = entity at `handle` in that file, else the Data named `nameInArchive`. All-empty + handle 0 = null link | 3,497 ok |

Unresolved link categories (all expected): 130 archives absent from the shipped data (editor `.fox`, `.las`, mis-filled names like `afgh_common_terrainMaterial`), 54 `*_PhysicsData` targets that the engine creates at load from `PhObjectDesc`/`PhxAssociation` [I], 1 stale link (handle 0, target Data removed from the only copy of `afgh_powerPlant_asset.fox2`).

## Notes
- Several asset paths exist in multiple packages (e.g. `mbt.ph` ×6); the copies differ in addresses but share names. The loader keys files by inventory path and maps each asset path to the first copy loaded.
- Dynamic properties (165 entities game-wide) are kept in `Entity.dynamic`.

## Runtime instantiation (exe, 2026-10-21) [V static]
Load path: `LoadDataSetFile` (Lua) → resource system (`FUN_1400CDF40`, status +0x44) → `EntityFile` (desc 0x142B661D0, 0x70 B; `DataSetFile2` derives, vtable 0x1420D0D00) → reader object at EntityFile+0x60 (0x140189xxx, async job `FUN_1401B13B0` or sync `FUN_1401893A0`) → **format selection `FUN_1400ED040`**: byte 0 == 0xF2 and bytes 1–3 == "box" → **binary reader** (ctor `FUN_1400EABE0`, 0x178 B, vtable 0x1420C5308); otherwise the **XML reader** (`FUN_1400EADC0`, vtable 0x1420C52D0) — the engine also loads XML DataSets.
Binary reader vtable: +0x20 `FUN_1400EDE50` = **time-sliced step** (called repeatedly by `EntityFile::Update` 0x1400F7D20), +0x28 `FUN_1400F0680` = attach buffer (data, size) to the stream at +0xC8.
Step state machine (+0x50):

| State | Function | Work |
|---|---|---|
| 0 | `FUN_1400EDBC0` header + `FUN_1400EDB00` entity headers | header: `F2 'b' 'o' 'x'`, version char − '0' (supported list `FUN_1400EBED0`; 5–6 = hashed-string format, +0x171), 0, flag byte, flag byte (must be 0), u32 entityCount, u32 stringTableOffset, u32 entitiesOffset; string table `FUN_1400EE6E0`; per-entity header + class lookup `FUN_1400EEE00`. Then **one arena** `BlockHeapAlloc(Σ align_up(class.size), max align)` for every entity whose class has no custom creator (desc+0xC0 == 0) |
| 1 | `FUN_1400EEB80(i)` | one entity per step: place at the next aligned arena offset (desc+0xD0 size, +0xD8 align) or call the class factory (`FUN_1400EB970`) when desc+0xC0 ≠ 0; read **static properties in class order** (iterator `FUN_1400754E0`), skipping hidden ones (PropertyInfo+0x2C bit 0), each via `FUN_1400EF250` |
| 2 | `FUN_1400EBF80` | second pass per entity: create the dynamic-property holder (desc+0x90 → vt+8), read `dynamicCount` dynamic properties (`FUN_1400EF210`), finish entity `FUN_1400EBC30` |
| 3 | `FUN_1400725F0` | post-load pass on the DataSet object [I: reference fixups] |
| 4 | `FUN_1400ECE70` | finalize / done |

The binary writer is `FUN_1400EF290` (DataSetFile2::Save): mirror image of the above (writes version as `'0'+5`).
Consequences for the engine: a DataSet is one contiguous allocation; file `address` fields are editor-session addresses (unique per build), mapped to new objects at load [I]; property order on disk = class-chain order (matches `TypeDB.properties()`).

## Live gate (2026-10-21) [V]
In Afghanistan free roam (mission 30010) every link of f30010's two `DataIdentifier`s (`CheckPointIdentifier` ×16 checkpoint Locators, `f30010_sovietBase_DataIdentifier` ×1) was queried in the running game over the IH pipe (`DataIdentifier.GetDataWithIdentifier(identifier, key)` → `name`, `IsKindOf(class)`, `worldTransform.translation`). **17/17 match the static graph** (name, class, translation to 1e-3; world = local transform composed up the `parent` chain). Capture: `Tools\capture_identifier_fixture.py` → `Engine\tests\fixtures\f30010_identifiers.json`; verifier `test_live_f30010_identifiers.py`.
Lua access confirmed: Data properties are readable by name from Lua (`d.name`, `d.worldTransform`), `IsKindOf` works on class names — a cheap channel for future fixtures.

---
<small>Source: `docs/engine/Entities.md` in the project repository &middot; generated 2026-10-28.</small>
