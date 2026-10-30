# GEOM collision

Codec: `Engine\formats\foxdata.py` (container + raw payloads) · verifier `Engine\tests\test_foxdata_all.py` (slow) · quick `test_m7_formats.py`.
**Gate (2026-10-29): 5,176 / 5,176 unique files round-trip byte-identically with zero undecoded bytes outside node payloads**: `.geom` 3,078 (8,000 entries, mostly `chunk2/3.dat`, environ / gimmick `scenes`), `.geoms` 2,033 (2,092; `block_*/..._geoprim_*.geoms`), `.gskl` 65 (202; item / chara skeletons).
Typed payload decoding (GeoGroup / GeoBlock / shape trees / bounding-volume grid) is **not done**: it is needed by the collision queries (M9 native boundary), and stays open as E30.

## Container [V via FOXDATA.md, D]
- Header: version 201406020, name hash 0x006B936E (`GEOM` per the template), flags 0, bytes 0x18–0x1F non-zero in every file (not read by the FoxData readers; [?]).
- Names are **GeoNameHash**, not StrCode32 / StrCode64 / the MGS4 24-bit hash (`GEOM` / `BLOCK` checked) [V by test]; no strings stored. Function [?].
- Topology [D]: `.geom` = root (flags 0x10) with one child group (flags 6) or bounding-volume + group (flags 0), plus usually a flags-0x40 sibling root (`10(6) 40(6)` 1,719 · `10(6) 40(0)` 835 · `10(0) 40(0)` 279 · `10(6)` 151 …). `.geoms` = 1–8+ roots `10(6)`. `.gskl` = group (6) + bone nodes (flags 0xB).

## Payloads [D layout checks; I meaning from the template]
| Node flags | Payload | Check over all files |
|---|---|---|
| 0x10, 0x40 | none | — |
| 0x6 | GeoGroup: GeoBlock chain (32-byte records, byte 0 = isFinal, u8 headerCount, u16 headersSize, …, u32 vertexBufferOffset, u32 headersOffset, u32 nextSectionOffset, GEO tags) then the material section | every flags-6 payload starts with ≥ 1 block (geom 3,780, geoms 8,091, gskl 265) [D] |
| 0x0 | GeoBoundingVolume (corner, extents, cell size, cell counts, u32 nextSectionOffset at +0x1C, cell lists) then GeoGroup | nextSectionOffset inside the payload and followed by a block chain: geom 1,487 / 1,487, geoms 2,145 / 2,145 [D] |
| 0xB | GeoBone: u32 GeoNameHash, u32 nameLength, char name[] | 265 / 265 lengths inside the payload [D] |

Shape headers (AABB / POLY prims, child / next offsets in 16-byte units), vertex headers (own vertices or FMDL vertex buffer) and the tag bit sets (`GEO_TRAP_TAGS`, `GEO_COL` …) follow `geom_geoms_gskl.bt` / `geo_common.bt` as leads [I].

## Exe side
`GeoGeomFile` class string 0x1424E3AE8, type registration 0x141B91670 (type info 0x142C75EF0) [V]; the payload parser itself is not located [?] (the template's 0x141BEF7B2 lies in the runtime geo manager 0x141BEF4D0, not a file reader).

## E7 (`*_PhysicsData`) is not a geom question
The 54 unresolved `*_PhysicsData` links of the s10151 graph live in `.ph` (`PhxAssociation.physicsData`) and `.sim` (`SimOnPhysics.physicsData`) files, which are FOX2 DataSets (magic `\xF2box`, M1 codec). See [`docs/engine/Entities.md`](../engine/entities.md) "Physics data links".

---
<small>Source: `docs/formats/GEOM.md` in the project repository &middot; generated 2026-10-30.</small>
