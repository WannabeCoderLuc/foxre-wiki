> [!NOTE]
> Generated `from[`docs/formats/FOX2.md`](https://github.com/WannabeCoderLuc/mgsvtpp-foxre/blob/main/docs/formats/FOX2.md)` on 2026-10-21. Edit the source doc; this page is overwritten on every sync. · [ Home](index.md) · [ Roadmap](Roadmap.md)

# FOX2 — Fox Engine DataSet

Codec `Engine\formats\fox2.py` · verifier `Engine\tests\test_fox2_roundtrip.py` · census `python Tools\fox2_census.py` (→ `Memory\research\fox2_census\census.json`).
**Gate (2026-10-21): 44,994 / 44,994 unique DataSets round-trip byte-identically** (46,215 inventory entries; 924 MB).
Tags: [V] round trip on every file + exe, [D] holds in every game file (census), [I] inferred, [?] unknown.

## Files
The same container is used under 15 extensions [D]: `.fox2` 38,837 · `.parts` 2,176 · `.tgt` 1,561 · `.vfxlf` 706 · `.sim` 408 · `.ph` 393 · `.phsd` 323 · `.sdf` 323 · `.fsd` 181 · `.veh` 32 · `.clo` 22 · `.des` 20 · `.bnd` 9 · `.vfx~1` 2 (unique counts). Engine class: `DataSetFile2` (StrCode64 0x7286073100F1; class descriptor 0x142B6AF60, object vtable 0x1420D0D00, size 0x80, `OnLoad` = vtable +0x48 0x140113750) [V].

All integers little-endian. All names are **StrCode64** (48-bit; upper 16 bits of every stored hash are 0 [D]); `Engine\core\strcode.py` is verified against the exe.

## Layout
```
Header (32 bytes)
 0x00 u32 magic 0x786F62F2 ("\xf2box") [D]
 0x04 u32 version 53 [D]
 0x08 i32 entityCount
 0x0C i32 stringTableOffset
 0x10 i32 entitiesOffset always 32 [D]
 0x14 12 bytes zero [D]
Entities (entityCount, back to back)
String table
 repeated { u64 hash; i32 length; u8 utf8[length] } (no NUL, no padding), terminated by 8 zero bytes
 pad to 16, then "\0\0end", pad to 16 [D]
```

### Entity (64-byte header + properties)
| Off | Type | Field | Notes |
|---|---|---|---|
| 0x00 | u16 | headerSize | 64 [D] |
| 0x02 | u16 | unknown1 | **constant per class** (317/317 classes, 0 exceptions) [D]; not the native instance size (TexturePackLoadConditioner: 72 vs alloc 0x80 in factory 0x1404BCCF0) [V]; meaning [?] |
| 0x04 | u16 | 0 | [D] |
| 0x06 | u32 | tag | `"ent\0"` 0x00746E65 [D] |
| 0x0A | u32 | address | file-local entity id, 16-byte aligned (low 4 bits 0 in all 2.3 M entities) [D]; target of EntityPtr/EntityHandle values |
| 0x0E | u32 | 0 | [D] |
| 0x12 | i32 | unknown2 | 0 in 11 % of entities, otherwise small increasing values per file (deltas 1–11 dominate) [D]; editor/serial id [I] |
| 0x16 | i32 | 0 | [D] |
| 0x1A | u16 | classVersion | 0 for 91 % of entities [D] |
| 0x1C | u64 | classHash | StrCode64 of the class name |
| 0x24 | u16 | staticCount | |
| 0x26 | u16 | dynamicCount | dynamic properties on 0.25 % of entities [D] |
| 0x28 | i32 | staticOffset | 64 [D] (relative to entity start) |
| 0x2C | i32 | dynamicOffset | 64 + size(statics) [D] |
| 0x30 | i32 | nextOffset | 64 + size(statics) + size(dynamics) [D] |
| 0x34 | 12 bytes | zero | [D] |

### Property (32-byte header + payload)
| Off | Type | Field |
|---|---|---|
| 0x00 | u64 | nameHash (StrCode64) |
| 0x08 | u8 | dataType (table below) |
| 0x09 | u8 | container: 0 StaticArray, 1 DynamicArray, 2 StringMap, 3 List |
| 0x0A | i16 | count |
| 0x0C | u16 | payloadOffset = 32 [D] |
| 0x0E | u16 | nextOffset = 32 + payload size padded to 16 [D] |
| 0x10 | 16 bytes | zero [D] |

Payload: `count` values back to back, padded to 16 at the end. **StringMap:** each entry `{u64 keyHash; value}` padded to 16 individually.

| id | type | bytes | id | type | bytes |
|---|---|---|---|---|---|
| 0 | int8 | 1 | 13 | EntityPtr | 8 (entity address) |
| 1 | uint8 | 1 | 14 | Vector3 | 16 (x,y,z + pad float) |
| 2 | int16 | 2 | 15 | Vector4 | 16 |
| 3 | uint16 | 2 | 16 | Quat | 16 |
| 4 | int32 | 4 | 17 | Matrix3 | 36 |
| 5 | uint32 | 4 | 18 | Matrix4 | 64 |
| 6 | int64 | 8 | 19 | Color | 16 |
| 7 | uint64 | 8 | 20 | FilePtr | 8 (path hash) |
| 8 | float | 4 | 21 | EntityHandle | 8 (entity address) |
| 9 | double | 8 | 22 | EntityLink | 32: packagePath, archivePath, nameInArchive hashes + handle |
| 10 | bool | 1 (0/1 only [D]) | 23 | PropertyInfo | [?] never seen |
| 11 | String | 8 (StrCode64; literal in string table) | 24 | WideVector3 | 16: 3 floats + 2 u16 |
| 12 | Path | 8 (StrCode64) | | | |

Usage (property instances over all files) [D]: EntityHandle 3.57 M, EntityPtr 2.28 M, Vector3 2.05 M, String 1.33 M, uint32 1.02 M, Quat 1.00 M, float 0.83 M, bool 0.28 M, FilePtr 0.18 M, int32 0.15 M, EntityLink 0.15 M, Path 61 k, uint8 40 k, Color 24 k. Containers: StaticArray 11.8 M, List 0.63 M (EntityHandle only), DynamicArray 0.54 M, StringMap 55 k.

## Codec notes
- Floats are kept as raw 32-bit patterns (exact round trip incl. NaN payloads); `to_json()` shows them as floats.
- Hashed values (String/Path/FilePtr/EntityLink) are raw integers; `Names` resolves them for display from the file's string table, dictionaries and `strcode64`.
- The writer emits the canonical layout above; since every game file is canonical, `write(read(b)) == b` holds for all of them.

## Exe side
- The loader does **not** validate magic, `ent` or `end` (none of these constants occur in `.xtext`) [V]: offsets are trusted.
- Parsing happens in the generic resource loader before `DataSetFile2::OnLoad` (0x140113750 casts the loaded object via `FUN_1401071B0` and stores it at +0x70) [V]. The byte parser itself is not yet located [?] — next: follow the resource factory that calls vtable +0x48.
- [docs/ENGINE.md](Engine-Core-Architecture.md) §1.2/§1.3 (FoxRe agent) give a different header/entity layout: **wrong [x]**, superseded by this spec.

## Open
unknown1 / unknown2 meaning; PropertyInfo encoding (type 23 unused in TPP data); exe parser VA.
