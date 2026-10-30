# FoxData containers

Codec `Engine\formats\foxdata.py` · verifier `Engine\tests\test_foxdata_all.py` (slow) · quick `test_m7_formats.py`.
**Gate (2026-10-29): 9,340 / 9,340 unique files round-trip byte-identically**: `.htre` 4,162 (4,209 entries) · `.tre2` 2 · `.geom` 3,078 (8,000) · `.geoms` 2,033 (2,092) · `.gskl` 65 (202). Typed payloads: terrain → `HTRE.md`, collision → `GEOM.md`.

Exe readers [V static]: node lookup by name (depth-first through child, then next) 0x1401A5C10 · parameter lookup 0x1401A5D00 · big-endian swap walker (defines every field width) 0x1401FB4B0 · header endian check 0x1401F9840 / swap 0x1401FB000. Lead: `FoxData_common.bt` (FoxEngineTemplates, MIT).

## Header (0x20 bytes, little-endian on PC) [V]
| Off | Type | Field |
|---|---|---|
| 0x00 | u32 | version: htre 3 / 4, tre2 4, geom family 201406020 (a date) [D] |
| 0x04 | u32 | nodesOffset (0x20 in every file) [D] |
| 0x08 | u32 | fileSize (= file length) [D] |
| 0x0C | Name | file name: `terrainHighBlock` (htre), `tre2`, GeoNameHash 0x006B936E (`GEOM`, template) — checked by the terrain loaders [V] |
| 0x14 | u32 | flags (0 in every file) [D] |
| 0x18 | 8 bytes | not read by any loader; zero in v3 htre, uninitialised memory in v4 htre / one tre2 / every geom [D] (kept raw) |

## Name (8 bytes) [V]
`u32 hash` (StrCode32 in terrain files; GeoNameHash in the geom family, function not identified [?]) · `u32 stringOffset`, **signed**, relative to the Name itself (0 = no string; cypr `.tre2` has negative offsets, strings stored at the end) [D]. Loaders compare only the hash [V].

## Node (0x30 bytes) [V]
| Off | Type | Field |
|---|---|---|
| 0x00 | Name | name |
| 0x08 | u32 | flags (type id in v4 terrain: heightMap 0, comboTexture 1, lodParameter 2, minHeight 3, maxHeight 4, materialIds 5, editParam / configrationIds 6, layoutDescription 8, patchDescription 9; 0 everywhere in v3 / afgh tre2) [D] |
| 0x0C | i32 | dataOffset, relative to the node (0 = no payload) |
| 0x10 | u32 | dataSize |
| 0x14 | i32 | parent (relative) |
| 0x18 | i32 | child (relative, 0 = none) |
| 0x1C | i32 | previous (relative) |
| 0x20 | i32 | next (relative, 0 = last) |
| 0x24 | i32 | parametersOffset (relative, 0 = none; negative in cypr `.tre2`) [D] |
| 0x28 | 8 bytes | zero padding [D] |

**HTRE v3 lists are cross-linked [D, 1,607 files]:** `editParam`'s child points to `configrationIds` at the end, whose siblings are reached again through the main `next` chain; parents point back to `editParam`. The v3 loader 0x1401FA720 starts at the first node's `next` [V]. The codec visits every node once by offset and writes each structure back where it was read.

## Parameter [V 0x1401FB4B0]
`u16 type` · `i16 next` (relative, 0 = last) · Name name · value at +0x0C: type 0 u32 (0x10 bytes), type 1 Name (0x14 bytes), type 2 f32 (0x10 bytes).

## Writer
Layout-preserving: header, nodes, parameters, strings and payloads go back to their offsets; bytes that no structure covers stay in `File.gaps` (non-zero runs only). After the typed terrain layer the only gaps left are uninitialised alignment padding (`HTRE.md`); geom-family files have no gap bytes at all [D].

---
<small>Source: `docs/formats/FOXDATA.md` in the project repository &middot; generated 2026-10-30.</small>
