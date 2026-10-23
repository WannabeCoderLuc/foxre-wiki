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
- Then come the tail block (first u16 = its size; opaque [?], holds a 48-bit hash), the grid, and the extra block.
- **Mesh types** = agent classes: 0, 1, 2, 4, 5 and 0x8004 occur.
  - afgh tiles carry 3–5 types (type 4 is the largest mesh).
  - The arena has only type 4.

## Quantisation [V]
- `world = origin + q × (dimX·cell/65536, 1/512, dimZ·cell/65536)`.
- Arena: 1 m = 102.4 q. afgh tile: 1 m = 504 q.

## kind 1: walkable triangle mesh [V]
- **Header:** u32 off[0..5] = (verts 0x20, polyInfo, polyRecords, 0, 0, 0); u16 nPoly at +0x18, u16 nVert at +0x1A.
- **Vertices:** u16 xyz, stored **per region, contiguous** (the region start is in kind 4).
- **polyInfo:** nPoly × u32 = `region << 20 | recordOffset/2`. Polygons are sorted by region.
- **Record** (16-byte aligned slot):
  - `u16 nb[3]` = neighbour across edge k, where edge k = corner k → k+1. Values: 0xFFFF = open border; 0x4000|i = adjacent-tile link.
  - `u8 corner[3]`, region-local.
  - `u8 edgeNode[3]` = kind-0 node of edge k, region-local.
  - If any neighbour is a tile link: `u16 ext[3]`, making a 32-byte slot.
  - The last record absorbs the body padding.
- All polygons in the game are triangles.

## kind 0: portal-node graph (path search) [V]
- **Header:** u32 off[0..8]; u16 nNode, nLink, 0, 0, 0, nRegion at +0x24.
- **off[0]** nodes: u16 xyz = **midpoint of triangle edge** (region, edgeNode). A cross-region edge has one node in each region at the same position (portal twins).
- **off[1]** info: (u16 adjStart, u16 region, u8 degree 2|4, u8 portal flag). Arena: 832 portal nodes.
- **off[3]** adjacency: degree × (u16 otherLocal, u16 linkLocal), plus 1 × u16 **twin global node** for portals.
- **off[2]** links: (u16 weight, u8 region, u8 0, u8 localA, u8 localB). There are 3 links per triangle: consecutive edge pairs.
  - **weight² ≈ a(dx² + dz²) + b·dy²** in quantised units, with √a ≈ 0.2484 (0.2424 in the arena) and √b ≈ 0.05–0.06. Weights are tile-relative.
- **off[6]:** u16 per region, the region attribute (1) [?].
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
<small>Source: `docs/NAVMESH.md` in the project repository &middot; generated 2026-10-23.</small>
