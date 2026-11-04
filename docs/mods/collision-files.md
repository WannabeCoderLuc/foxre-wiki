# Terrain and collision files in a mod

*Based on: [Terrain and collision files](../explain/terrain-and-collision.md) (M7, PASS). Exact details: [FoxData containers](../formats/foxdata.md), [GEOM collision](../formats/geom.md), [HTRE / TRE2 terrain](../formats/htre.md). For heights at a point see [Ground height at any point](ground-height.md).*

## The findings
- Terrain (`.htre`, `.tre2`) and collision (`.geom`, `.geoms`, `.gskl`) use **one container format, FoxData**: a header, then a tree of named nodes, each with an optional payload and a list of typed parameters [V: the game's readers]. 9,340 of 9,340 files round-trip byte for byte [V].
- Node and parameter names are **hashes**: StrCode32 in terrain files, a separate "GeoNameHash" in collision files whose function is not identified [?]. Loaders compare only the hash [V].
- Links inside the tree (parent, child, next, payload, parameters) are **relative offsets**, so moving a structure means rewriting the offsets that point at it [V].
- Terrain payloads are decoded: heights, patches and their placement on the map [V live].
- **Collision shape payloads are not decoded yet** (E30). The container and the block chains inside it are checked on every file [D]; what each shape is and how the game queries it is open.
- `.gskl` files are bone lists for items and characters, not world collision [D].
- `*_PhysicsData` links in levels point to `.ph` and `.sim` files, which are ordinary DataSets, not geometry [V].

## Where the files are
| Type | Count (unique) | Where |
|---|---|---|
| `.htre` | 4,162 | one per 128 m terrain block, e.g. `afgh_<bx>_<bz>_terrain.htre` |
| `.tre2` | 2 | coarse terrain for a whole location (every 16th height) |
| `.geom` | 3,078 | mostly environment and gimmick scenes |
| `.geoms` | 2,033 | per-block primitive collision (`block_*/..._geoprim_*.geoms`) |
| `.gskl` | 65 | item and character skeletons |

## What you can and cannot do today
| Task | Possible from these specs? |
|---|---|
| Read terrain heights, build a height map image | yes |
| Edit terrain heights and write a valid file | the container and height layout are known [V]; whether collision follows edited terrain in game is untested |
| Rename, copy or re-pack collision files byte-exactly | yes, at container level |
| Read collision shapes (boxes, polygons) | not yet: payload layout follows community templates as leads only [I] |
| Ask "what does a ray hit here" offline | no; planned with M14 Collision and physics |

## How this would be used in a mod
*Hypothetical example; not built or tested.* A map-viewer mod draws every collision file's node tree for one terrain block, so a modder can see which `.geoms` covers which area before editing anything.

```python
# hypothetical: walk a FoxData tree (any reader that follows the FoxData spec)
def walk(node, depth=0):
    print("  " * depth, hex(node.name_hash), "flags", hex(node.flags), "payload", node.data_size)
    for child in node.children():
        walk(child, depth + 1)
```
A file with flags `0x10` at the root and a child with flags `6` holds a group of collision blocks; flags `0` adds a bounding-volume grid in front of the group [D]. Listing these per block is safe, read-only, and already possible.

## Pitfalls
- **Bytes 0x18 to 0x1F of the header** hold leftover memory in most files and are read by no loader [D]. Keep them as they are; do not "clean" them, or your file will differ from the original for no reason.
- HTRE version 3 files have cross-linked node lists (one node reached twice through different links) [D]. A naive tree walk visits nodes twice or loops.
- Cyprus `.tre2` uses negative string offsets [D]. Treat offsets as signed.
- Rocks and buildings are collision, not terrain. The terrain height under a rock is the ground below it.

---
<small>Hand-written article (`docs/site/mods/Collision-Files.md`) &middot; published 2026-11-05.</small>
