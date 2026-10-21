> [!NOTE]
> Generated `from[`docs/engine/Entities.md`](https://github.com/WannabeCoderLuc/mgsvtpp-foxre/blob/main/docs/engine/Entities.md)` on 2026-10-21. Edit the source doc; this page is overwritten on every sync. · [ Home](index.md) · [ Roadmap](Roadmap.md)

# Entities: DataSets → typed entity graph

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

## Open (rest of M2)
- How the runtime instantiates these entities (factory per class, writes fields at the EDB offsets, DataSet+0x78 name map, link resolution across packages at load) — `fox-system`.
- Live fixture of one loaded DataSet (entity count + field values) — `fox-ground-truth`.
