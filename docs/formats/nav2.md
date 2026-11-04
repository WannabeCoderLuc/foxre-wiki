# NAV2 navmeshes

**Sources:**

- 853 `.nav2` files under `EXTRACTED_DATA`, compared field by field (`Tools/nav2_probe*.py`).
- `NavxNavBlock` entities in the fox2 index.
- Engine class names (`Navx*` strings in the exe).

**Tool:** `Tools/navmesh_tool.py`.

**Evidence tags:**

- **[V]** consistent across all files tested and checked against known world positions
- **[I]** inferred
- **[?]** unknown

## Loading chain [V]
- A **`NavxNavBlock`** entity (in a block `.fox2`) holds `worldName`, `filePath` (`.nav2`), `tileId`, `sceneName`, and hole-simplification parameters. A world is the set of all blocks sharing a `worldName`.
- **Only 3 worlds exist in the game:**
  - `""` (StrCode64 `0xB8A0BF169F98`): 666 tiles, the whole map, used by soldiers and vehicles.
  - `sky` (`afgh_common_navi_sky.nav2`): air.
  - `sahelan` (`s10151_nav_sahelan.nav2`): the Ep31 arena only.
- Agents bind to a world by name when their `TppNavigationController` is created. The Sahelan passes `"sahelan"` (0x1418BAE48) and Heli2 uses `sky`.

## Status (2026-10-17, end of the navmesh pass)
- **Fully decoded, and the writer is byte-identical** on all 853 game files.
  - `Tools/nav2lib.py selftest`: 0 failures; 2,799 meshes decode and re-encode unchanged.
- **Rules re-derived from the triangle mesh and checked on all 2,799 meshes:**
  - region AABB: exact (2,799/2,799);
  - node = edge midpoint: within 1 unit (2,776/2,799);
  - links = consecutive edge pairs of each triangle: 2,798/2,799.
- **Engine-computed values** (link weights, region-link costs) are fitted, not exact. Edits therefore rescale the stored values instead of recomputing them.
- **Tools:**
  - `Tools/nav2lib.py`: library.
  - `Tools/navmesh_tool.py`: commands `tris`, `regions`, `edit`, `roundtrip`, plus the older ones.
  - `Tools/nav2_validate.py`: rule checks.
  - `Tools/_evidence/nav2_probes/`: decode evidence (probes 11-23, run from that folder with Tools on PYTHONPATH).

## Container [V]
| Offset | Type | Meaning |
|---|---|---|
| 0x00 | u32 | magic `0x0C012B6A` (`0x0C012B69` in 2 sky files; same layout) |
| 0x04 | u32 | file size |
| 0x08 | u32 | header size (0x70 empty, 0x90 for 1 mesh type, up to 0x120) |
| 0x0C | u32 | chunk count (4 per mesh type) |
| 0x10 | u32 | spatial **grid** offset |
| 0x14 | u16, u16 | 0, tile id |
| 0x18 | u32 | **tail** block offset |
| 0x20 | f32×3 | tile origin (world) |
| 0x2C | u32 | optional extra block (mtbs) |
| 0x44 | u16×4 | [?] |
| 0x4C | u8 | flags [?] |
| 0x50 | 16 bytes | GUID [?] |
| 0x60 | u32 | number of mesh types |
| 0x64 | 12-byte entries | **section table**: (u16 meshType, u16 tile, u32 body offset, u32 chunkSize<<8 \| kind), for kinds 0, 3, 1 |

- After the header come **chunks**. Each chunk has a 16-byte prefix `(u32 kind, u32 size incl. prefix, u32 16, u16 meshType, u16 tile)` followed by its body.
  - Order: kind 0 for every type, then kind 1, then kind 4, then kind 3.
  - Kind 4 is not in the section table.
- Then come the tail block, the grid, and the extra block.
- **Tail block** = one cluster graph per class, each starting with its u16 size [V 0x141CCE3F0]: +2 nodes offset, +4 node count, +6 links offset, +0xC border table (6 bytes: T, start, count), +0xE ext2 (4 bytes: cost, other). Node 14 bytes: u16 x, y, z, attr at +6, link offset at +8, nx at +0xA, n1 at +0xC, n2 at +0xD. Opposite border table 0x142517238 = (2, 3, 0, 1). A region's cluster = kind 3 record +4 + class * 2; soldiers use class 0 [D].
- **Mesh "types" are tile pieces, not agent classes (2026-10-30, corrected) [V static + D].** The chunk's (u16 type, u16 tile) is one little-endian u32 id = `tile << 16 | type`, used as `T << 15 | piece`: **T = tile * 2 + (type >> 15)** is the full tile index (bit 15 of "type" is T's low bit, so adjacent blocks share a `tile` value), **piece = type & 0x7FFF**. Decoders: 0x141C7C610 (id -> mesh; `id >> 15` hashed by 0x141C88590 to a tile row, `id & 0x7FFF` = column), 0x141CA4A90.
  - piece 0-3 = thin stitch strips along the tile's four borders (0 z-min, 1 x-max, 2 z-max, 3 x-min) [D 140_142, 128_136]; 4 = the inner mesh of `_nav.nav2`; 5 = the inner mesh of `_nav.1.nav2` (camp packs). The old reading "soldiers use types 4 and 5" only saw the inner pieces.
  - `(T & 0xC000) == 0x8000` = a runtime tile with float vec4 node positions, not from a file [V static 0x141C7FA20].

## Tile placement = the M7 terrain block grid (2026-10-29) [D]
- Tile `<loc>_<bx>_<bz>_nav*.nav2` has header origin x = (bx - 133) * 128, z = (bz - 133) * 128 exactly, the same block origin as the terrain ([`docs\formats\HTRE.md`](htre.md), `Engine\world\heightfield.py`): **779 / 779 unique afgh / mafr tiles**; first name number = x, second = z (as M7). Origin y = the tile's height base (e.g. 292.8 for afgh_147_129).
- Grid extent 13 x 13 cells of 10 m = 130 m (2 m overlap into the next block) on 708 tiles; the other 71 have no grid and no mesh (empty files).
- A tile is split over two files: `NavxNavBlock` has `isSplit`, `filePtr` (small block `_nav.nav2`) and `remainingFilePtr` (large block `_nav.1.nav2`) [D].

## Quantisation [V]
- `world = origin + q / (xq, yq, zq)`, the u16s at header +0x44, +0x46, +0x48 (afgh x and z: 511 on nearly all files; y varies per tile) [V 2026-10-31: with this scale our A* node lists equal the live ones on every search that finished]. The older `dimX·cell/65536` (504 q/m) was up to 1.8 m wrong at the far edge of a tile and caused false holes and wrong start triangles.
- u16 at header +0x4A = link weight units per metre [V 0x141CB83E0].

## kind 1: walkable triangle mesh [V]
- **Header:** u32 off[0..5] = (verts 0x20, polyInfo, polyRecords, 0, 0, 0); u16 nPoly at +0x18, u16 nVert at +0x1A.
- **Vertices:** u16 xyz, stored **per region, contiguous** (the region start is in kind 4).
- **polyInfo:** nPoly × u32 = `region << 20 | recordOffset/2`. Polygons are sorted by region.
- **Record** (16-byte aligned slot):
  - `u16 nb[n]` = neighbour across edge k, where edge k = corner k → k+1. **Link word [V static 0x141CA4A90]:** 0xFFFF = open border; top 2 bits 0 = same mesh, triangle `v & 0x3FFF`; 1 (`0x4000|i`) = triangle i of piece `ext1[k]` in the same tile; 2 (`0x8000|i`) = triangle i of piece `ext1[k]` in tile T = `ext2[k]`; 3 = off-mesh table entry.
  - `u8 corner[n]`, region-local.
  - `u8 edgeNode[m]` = kind-0 node of edge k, region-local.
  - polyInfo bits: 0-17 record offset / 2, 18: n = 4 (else 3), 19: m = 4 (else 3), 20-31 region [V static 0x141CA4EF0].
  - If any neighbour is a tile link: `u16 ext1[n]` at record + 2n + ((n - 3 + 7 + m - 3) & ~1), then `u16 ext2[n]`, making a 32-byte slot.
  - The last record absorbs the body padding.
- All polygons in the game are triangles.

## kind 0: portal-node graph (path search) [V]
- **Header:** u32 off[0..8]; u16 nNode, nLink, 0, 0, 0, nRegion at +0x24.
- **off[0]** nodes: u16 xyz = **midpoint of triangle edge** (region, edgeNode). A cross-region edge has one node in each region at the same position (portal twins).
- **off[1]** info: (u16 adjStart, u16 region, u8 degree 2|4, u8 portal flag). Arena: 832 portal nodes.
- **off[3]** adjacency [V static search 0x141CB83E0]: at `2 * (((region & 0xF000) << 4) | adjStart)`: degree × (u16 other node, u16 link), then by the info flag byte: bit 0: u16 twin node in the same mesh; bit 1: (u16 piece, u16 node) in the same tile; bit 2: (u16 T, u16 piece, u16 node) in another tile. Flag bits 3-4 = node kind (non-zero: never relaxed, 0x141C7F850). Region low 12 bits of the info u16 are the region, high 4 extend adjStart.
- **off[2]** links: (u16 weight, u8 region, u8 0, u8 localA, u8 localB). There are 3 links per triangle: consecutive edge pairs.
  - **weight² ≈ a(dx² + dz²) + b·dy²** in quantised units, with √a ≈ 0.2484 (0.2424 in the arena) and √b ≈ 0.05–0.06. Weights are tile-relative.
- **off[6]:** u16 per region, the region attribute bits (afgh e.g. 0x4E1, 0x4E9, 0x481): tested against the query's filter (search, raycast) and cost mask (+0xE0 -> multiplier +0xDC) [V static]. Bit meanings [?].
- Link cost = u16 weight / u16 at file header +0x4A [V static 0x141CB83E0].
- **off[8]:** u16 per node, a triangle owning the edge.
- Arrays are 16-byte aligned.

## kind 4: region tables [V]
- **Header:** u32 (0x10, off_sc, end, nRegion).
- **+0x10:** (u16 min xyz, u16 max xyz) = exact **AABB of the region's vertices**.
- **+off_sc:** (u16 start[4], u8 count[4]). The four columns are (kind-1 verts, kind-1 polys, kind-0 links, kind-0 nodes).

## kind 3: region graph (coarse search) [V]
- **Header:** u32 (off_rep 0x20, off_rec, off_stream, 0, end, nRegion); u16 **nPortal** at +0x1A.
- **off_rep:** u16 xyz = the region's **representative node** (one of its kind-0 nodes).
- **off_rec:** (u16 streamStart/2, u8 0, u8 linkCount), 12-byte slots.
- **Stream, per region:** linkCount × (u16 cost, u16 neighbourRegion, u8 nPortals, u8 **backIndex** = index of the reverse link in the neighbour's list), then the portal node ids (u8, local), padded to 2 bytes.
  - Arena: 620 directed links; neighbours, portals and back indices are 100% exact.
  - **cost ≈ mean shortest kind-0 path length** from the representative node to the link's portals. Exact for 75–91% of links; float rounding explains the rest.

## Spatial grid [V]
- **Header:** f32 origin, u32 maxY (q), u32 dims[3], u32 cell, u32 [?], u32 cellsOff, u32 listsOff, u32 end (16-aligned).
- **Cell** (8 bytes): u32 **self-relative** list offset, u16 group count, u8 minY>>8, u8 maxY>>8.
- **List:** per group, (u32 meshType, u32 n, u16 regionIds[n]) = the regions whose AABB overlaps the cell.

## Editing [V]
- **`navmesh_tool.py edit <tile> --box x0,z0,x1,z1[,y0,y1] (--raise dy | --move dx,dy,dz) --out f.nav2`**
  1. Moves the vertices in the box.
  2. Then updates:
     - affected nodes;
     - changed link weights, rescaled by the fitted metric;
     - the AABBs and representative points of the affected regions;
     - region costs, rescaled by the change in path length;
     - grid cells (cells only gain regions and widen height ranges).
  3. Re-parses the output before writing.
- **Test:** arena raised 5 m over 100 × 100 m. 112 vertices, 99 triangles and 14 regions affected; all rules still hold. Output: `Mods/_build/navtest/s10151_nav_sahelan_raised.nav2`. **Not yet tested in game.**
- **Not yet supported:** topology changes (add/delete triangles or regions), tile merges, new worlds. The layout above is complete enough to write them.
- **Render:** `navmesh_tool.py tris <tile> --out f.png [--mesh N|all]`. Outputs: `navmesh/sahelan_arena_tris.png`, `navmesh/afgh_113_120_tris.png`.

---
<small>Source: `docs/NAVMESH.md` in the project repository &middot; generated 2026-11-05.</small>
