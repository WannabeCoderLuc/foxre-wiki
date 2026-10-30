# HTRE / TRE2 terrain

Codec `Engine\formats\terrain.py` (over `FOXDATA.md`) · verifier `Engine\tests\test_terrain_all.py` (slow) · quick `test_m7_formats.py` · query `Engine\world\heightfield.py`.
**Gate (2026-10-29): 4,164 / 4,164 unique terrain files round-trip byte-identically, typed**: `.htre` v3 1,607 (cypr, afgh) + v4 2,555 (afgh, cypr), `.tre2` v4 2 (`afgh_common_terrain`, `cypr_common_ter`). Every v4 patch offset lands on its node's payload (2,557 / 2,557) [D].
Census: `.htre` 4,209 entries / 4,162 unique, 33,552–33,809 bytes, 4,096 in `chunk2.dat`, 113 in `chunk0.dat` (`location/<loc>/block_small|block_debug/.../<loc>_<x>_<z>_terrain.htre`); `.tre2` one per location in `block_common`.

## Loaders [V static]
Shared entry 0x1401F95B0 (from the resource's vt+0x48 0x1401F96D0; `htre` resource class vtable 0x1420FC5C0, factory 0x1401F9980 registered for extension `htre` by 0x1401FAF50): kind 1 → **TRE2** 0x1401FADD0, kind 2 → **HTRE** 0x1401FA490. Both reject files < 0x20 bytes, fix endianness, and check the header name hash (`tre2` 0x142B77218 / `terrainHighBlock` 0x142B77268).

- HTRE: version 1 → converter 0x1401F9CE0 then the v2 path 0x1401FA5C0; 2 → 0x1401FA5C0; 3 → 0x1401FA720 (builds the patch from the params); else (4) → 0x1401FACA0.
- TRE2: version 1 rejected; 2–3 → 0x1401F9CF0 (builds the layout from `param`'s params: width & ~31, height & ~31, highPerLow, maxLodLevel, gridDistance; heights ±200 default); 4 → 0x1401FA330.
- v4 patch reader (both) 0x1401F9A90.
Node-name hashes are static-init globals 0x142B771D0–0x142B77288 (strings at 0x1420FC690–0x1420FC750).

## Nodes
| Node | v4 htre (flags) | v3 htre | tre2 | Payload |
|---|---|---|---|---|
| heightMap | 0, params pitch 2, heightFormat 1, heightRangeMin/Max | params pitch 2 (+ a second `heightMap` without pitch = 64×64 RGBA weight map, template) | params heightFormat, heightRangeMin/Max | f32 heights, row-major |
| comboTexture | 1, param comboFormat 6 | — | yes | RGBA8 |
| editParam | 6, param maxLodLevel 4, no payload | same (flags 0) | — | — |
| lodParameter / param | 2 (80 B) | 64 B | `param`: width, height, highPerLow 16, maxLodLevel 4, gridDistance 2.0 | f32 per cluster × LOD |
| maxHeight / minHeight | 4 / 3 | 16 B each | yes | f32 per 32×32 cluster [D] |
| materialIds | 5 | 16 B | yes | RGBA8 |
| configrationIds (sic) | 6 | 16 B | yes | u32 per cluster |
| patchDescription / layoutDescription | 9 (htre) | — | 8 | header + patch |

All [D] across the census; sizes per kind are constant inside each group.

## Description headers [V]
- `patchDescription` (htre v4, 24 bytes): u64 0, u64 0, u32 1, **i32 patchOffset** at +0x14 → patch = +0x14 + offset (always +0x18) [D 2,555].
- `layoutDescription` (tre2, 0x2A bytes): u64, u64, u32 gridWidth, u32 gridHeight, **i32 patchOffset** at +0x18 → patch = +0x18 + offset; f32 maxHeight +0x1C, f32 minHeight +0x20, f32 gridDistance +0x24, u16 lodCount +0x28 (each field copied by 0x1401FA330). `afgh_common_terrain.tre2` declares only 24 bytes, the loader reads past it [V].

## Patch (0x52 bytes) [V 0x1401F9A90, D all v4 files]
| Off | Type | Field |
|---|---|---|
| 0x00 | u32 | heightFormat 1 (PC f32) |
| 0x04 / 0x08 | f32 | maxHeight / minHeight (world metres) |
| 0x0C / 0x10 | i32 / u32 | heightMap offset (self-relative) / size |
| 0x14 | u32 | comboFormat 6 |
| 0x18 / 0x1C | i32 / u32 | comboTexture offset / size |
| 0x20 | u64 | 0 |
| 0x28 / 0x2C / 0x30 / 0x34 / 0x38 | i32 | materialIds / configrationIds / maxHeight / minHeight / lodParameter (`param`) offsets, each relative to its own field |
| 0x3C | u32 | 0 in 2,366, 1 in 191 htre [?] |
| 0x40 | u32 | 0 |
| 0x44 / 0x48 | u32 | height / width of the height grid (htre 64 × 64; tre2 128 × 128 cypr, 256 × 256 afgh) |
| 0x4C | u16 | clusterGridSize 32 |
| 0x4E | u16 | **lowShift** = log2(highPerLow): 0 htre, 4 tre2; the loader computes cluster counts as `(height << shift) / 32 × (width << shift) / 32` [V]. (The template's "MaxLodLevel" is wrong.) |
| 0x50 | u16 | lodCount: htre 5, tre2 1 (cypr) / 5 (afgh) |

Bytes from 0x52 to the next 16-byte boundary are uninitialised memory [D] (kept raw, the only bytes the codec does not type).

Sizes [D]: min/maxHeight = 4 bytes per cluster; lodParameter = 5 × clusters × 4 (htre), `param` = 4 × clusters × 4 (tre2). The loader endian-swaps (lodCount − 1) × clusters floats of it [V]; the meaning of the extra LOD slot is [?].

## Heights
f32 absolute world heights in metres (afgh ~190–820, cypr ~−50–200) [D]. The declared ranges (patch min/max, heightRangeMin/Max) **are not bounds**: 418 afgh blocks hold samples above their range [D].

- **Storage order [D every kind]:** the heightMap payload is a grid of 32 × 32 clusters (clusterGridSize), clusters row-major, each cluster row-major (a 64 × 64 `.htre` = 4 clusters of 1,024 floats). Read as one plain row-major grid it jumps at rows 16 / 32 / 48 and column 32; untiled, neighbouring blocks continue with the in-block step (seam median 0.29 m = in-block 0.28 m) across all 4,096 afgh blocks. Same tiling in v3 `.htre` and both `.tre2`. `terrain.Terrain.heights()` returns the untiled grid.
- **World placement [V live]:** rows run along world z, columns along world x; small block `<loc>_<bx>_<bz>` covers x ∈ [(bx − 133) · 128, (bx − 132) · 128), z likewise (133 = the stage-block centre index, `World.md`); sample k lies at +2 k m, so the 64 samples tile the 128 m block with no shared edge (the cell between two blocks uses the neighbour's first sample). afgh blocks 101–164 span −4096…4096. Static cross-check: the 70 rat route points of `afgh_base.lua` lie within centimetres of the field.
- **`.tre2` [D]:** the low grid is exactly every 16th sample of the block mosaic (afgh 256 × 256 vs 4,096 × 4,096: median and max difference 0), spacing gridDistance × 2^lowShift = 32 m, origin −gridWidth · gridDistance / 2 = −4096. Every afgh small block has its `.htre`, so no walkable point is covered by the `.tre2` alone.

## Height queries (`Engine\world\heightfield.py`)
`HeightField(grid, spacing, origin_x, origin_z).sample(x, z)`, float32 over a contiguous row-major buffer (ROADMAP native boundary); `HeightField.from_blocks({(bx, bz): grid})` builds one field from small blocks, `HeightField.from_tre2(...)` the low field.

- **Interpolation [V live]:** each 2 m cell is two triangles split along the diagonal (x0, z0) → (x0 + 2, z0 + 2): with fx, fz the fractions in the cell and a, b, c, d = h[r,c], h[r,c+1], h[r+1,c], h[r+1,c+1]: fx ≥ fz → a + (b − a)·fx + (d − b)·fz, else a + (d − c)·fx + (c − a)·fz.
- **Live fixture** (`Engine\tests\fixtures\m7_ground_heights.json`, `Tools\m7_ground_fixture.py`, run `Memory
esearch\m7_ground_20261029_182058`): f30010, IH pipe `TppPlayer.Warp` to (x, ground + drop, z), rest position from `vars.playerPos*` (no vanilla Lua or binding returns a ground height or raycast). 36 drops over 6 blocks (146–148 × 129–130): 24 on terrain of slope ≤ 12° rest at ground + 0.798 m within ±5 mm (drop 1 m or 4 m gives the identical Y); 4 steeper points rest 1–2 cm higher (controller contact, grows with sec slope); 8 rest on rocks / props. Bilinear (σ 6 cm) and the other diagonal (σ 12 cm) miss the live heights (`test_m7_ground.py`).

- Open (E32) [?]: the 0.798 m player offset and the ±5 mm scatter (likely the physics heightfield's quantisation), patch +0x3C, the extra LOD slot.

---
<small>Source: `docs/formats/HTRE.md` in the project repository &middot; generated 2026-10-30.</small>
