# Ground height at any point

*Based on: [Terrain and collision files](../explain/terrain-and-collision.md). Exact details: [HTRE / TRE2 terrain, "Heights", "Height queries"](../formats/htre.md).*

## The finding
The game's Lua has no function that returns the ground height at a point [V: no vanilla script or registered native does]. But the terrain files answer it exactly [V live, 24 points within 5 mm]:

- Block file `<loc>_<bx>_<bz>_terrain.htre` covers x from (bx − 133) × 128 to (bx − 132) × 128 and z likewise.
- Its 64 × 64 heights (2 m apart) are stored as four 32 × 32 tiles, each row by row; rows run along z, columns along x.
- Between samples the ground is two triangles per 2 m square, split from the (x, z) corner to the (x + 2, z + 2) corner.
- `vars.playerPosY` of a player standing on flat ground = ground + 0.798 m.

## How it works
For a point (x, z): find the block and the 2 m square, take its four corner heights a (x, z), b (x + 2, z), c (x, z + 2), d (x + 2, z + 2) and the fractions fx, fz inside the square:

- fx ≥ fz: height = a + (b − a)·fx + (d − b)·fz
- otherwise: height = a + (d − c)·fx + (c − a)·fz

## How this would be used in a mod
*Hypothetical example.* A mod places supply drops at random spots in Afghanistan and must put them on the ground, not under it or floating. Offline, a small tool reads the `.htre` blocks for the area (with our reader or your own, undoing the tiling) and writes a Lua table of (x, height, z) spots. In game the mod only looks them up:

```lua
-- generated offline from afgh_*_terrain.htre: {x, groundY, z}
local spots = { {1846.6, 332.884, -303.3}, {1969.5, 298.504, -483.0} }
local s = spots[math.random(#spots)]
TppPlayer.Warp{ pos = { s[1], s[2] + 0.8, s[3] }, rotY = 0 }   -- or place your object at s[2]
```
Adding 0.8 m to a player warp puts the player exactly where the game would rest them on flat ground, with no fall.

## Pitfalls
- Rocks, buildings and props are separate collision (`.geom`), not terrain: the terrain height there is the ground under the rock.
- Terrain collision loads with the map blocks around the player: in our test the first warp to a far-away spot fell through the ground, the same warp a few seconds later held. Warp, wait, then check `vars.playerPosY`.
- The coarse `.tre2` only has every 16th height (32 m apart): fine for a map, not for placing objects.
- Only Afghanistan (`afgh`, 4,096 blocks) and the Cyprus prologue (`cypr`, 113) have named `.htre` files in our data list; Africa's terrain files are among the archive entries whose names are still unknown.

---
<small>Hand-written article (`docs/site/mods/Ground-Height.md`) &middot; published 2026-10-30.</small>
