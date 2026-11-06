# Mod toolkit (MOD-A)

Code `Tools\moda\` (Python: tools stay Python by rule; no engine code). Verifier `Engine\tests\test_moda_toolkit.py`. Gate: [`docs\ROADMAP.md`](../status/roadmap.md) "Mod track", MOD-A G1-G4 (`gates.json` "MOD", items `MOD-A.G1` …).
Tags: [B Gk] built and checked by gate item k, [D] holds in every vanilla file, [V] exe / verified elsewhere (cited), [I], [?].
**State (2026-11-06):** G1 built (validated writers + `.frt` route editor). G2 built (navmesh baker + NAV2 rules). G3 mod-Lua harness, G4 live: not built.

## Principles [D]
- The toolkit never writes a file the engine's own loader would reject. Every write goes through one path: encode with the engine codec (`Engine\formats\`), decode the bytes again with the same codec, re-encode and compare (the bytes describe exactly the model that was meant), then run the format's rules. Any `error` rule refuses the write and nothing reaches disk; `warn` rules are reported and the file is written.
- Rules come from the format specs ([`docs\formats\FRT.md`](../formats/frt.md), `FOX2.md`, `FPK.md`): a rule tagged [V] is something the exe checks, [D] is an invariant every vanilla file keeps. An invariant whose break would leave data the engine cannot find or follow is an error; one whose meaning is still open is a warning.
- Every vanilla file passes every rule unedited and writes back byte-identically (`.frt` 307 / 307 in G1).
- Deterministic: same input, same bytes; no clocks, no randomness, sorted output.

## Writers [B G1]
`moda.writers.write(path, model, kind=None)` (kind from the extension) and `write_bytes(path, raw, kind=None)`:

1. `raw = codec.write(model)`; 2. `codec.write(codec.read(raw)) == raw` (rule `<FMT>-MODEL`), 3. `check(kind, raw)`; 4. errors → `Refused(report)`, else write to `path.tmp` and rename over `path` (no half-written file). Returns the `Report` (issues with rule id, severity, location, text).
Kinds: `frt`; `fox2` and its aliases (`.fox2 .parts .tgt .vfxlf .sim .ph .phsd .sdf .fsd .veh .clo .des .bnd .vfx~1`, FOX2.md); `fpk`, `fpkd`. A package is checked entry by entry with the entry's own rules (`.frt` entries as FRT, DataSet entries as FOX2); an entry's issues carry its path.

## Validation rules [B G1]
| Rule | Sev | Check | Basis |
|---|---|---|---|
| FRT-READ | error | magic `ROUT`, version 3, every table inside the file | loader 0x140513F70 accepts only v3 [V]; codec |
| FRT-MODEL | error | `write(read(b)) == b` | codec |
| FRT-COUNT | error | route / node / event counts and event table words fit u16 | header / definition / table widths [V layout] |
| FRT-ID-ORDER | error | route ids strictly ascending (sorted, no duplicates) | route lookup is a binary search (view slot +0x20, 0x140514100) [V]; 307 / 307 [D] |
| FRT-ROUTE-EMPTY | error | every route has a node | [D] |
| FRT-NODE-EDGE | error | every node has at least one event (its edge event) | [D] |
| FRT-TABLE | error | node tables are contiguous (start = sum of the previous counts) and use every event of the route once | [D] |
| FRT-EDGE-FIRST | error | first event of a node has isNodeEvent 0, the others 1 | [D 963,624 events] |
| FRT-FLAGS | error | isNodeEvent, isLoop in {0, 1}; aimType 0..4 | [D] |
| FRT-POS | error | node positions finite | [D] |
| FRT-BODY | warn | bodySection 0 (no vanilla event has another value; meaning unread) | [D] |
| FRT-TYPE | warn | event type is one of the 104 vanilla types, used in a role (edge / node) vanilla uses it in | census `Tools\moda\frt_event_types.json` [D] |
| FRT-CANONICAL | warn | raw file has the canonical layout (only for `check` of foreign bytes; writers always emit it) | [D 307 / 307] |
| FOX2-READ | error | magic `\xF2box` version '5', flags 0, entities and properties decode | FUN_1400ED040 [V]; codec |
| FOX2-MODEL | error | `write(read(b)) == b` | codec |
| FOX2-CLASS | error | class hash is a class of the type DB (`Engine\core\typedb.py`) or a class seen in vanilla data (`fox2_typedb.json`: the 17 `Fx*` classes the dump omits) | Reflection.md [V] |
| FOX2-CLASS-VERSION | error | classVersion equals the registry class version | load fails with 0x84E89055 otherwise [V] |
| FOX2-PROP | error | every static property exists in the class chain with the same type and container | `test_typedb.py` over all 44,994 DataSets [D] |
| FOX2-ADDR | error | entity addresses unique and non-zero | EntityPtr / EntityHandle targets [D] |
| FOX2-ADDR-ALIGN | warn | addresses 16-byte aligned | [D 2.3 M entities] |
| FOX2-HASH48 | warn | upper 16 bits of every stored name hash 0 | [D] |
| FOX2-BOOL | warn | bool values 0 / 1 | [D] |
| FOX2-CANONICAL | warn | canonical layout (foreign bytes) | [D] |
| FPK-READ | error | header `foxfpk` + kind + `win`, tables and strings inside the file | codec |
| FPK-MODEL | error | `write(read(b)) == b` | codec |
| FPK-NAME-DUP | error | no two entries with the same name | [D] |
| FPK-ENTRY | error / warn | an entry's own rules (FRT-*, FOX2-*), same severity | above |
| FPK-VERSION | warn | header version 2 | [D] |
| FPK-MD5 | warn | stored MD5 = MD5 of the stored name | 124,841 / 124,841 [D] |
| FPK-PATH | warn | entry names start with `/Assets/` | [D] |
| FPK-CANONICAL | warn | canonical layout (foreign bytes) | [D 16,354 / 16,354] |

## Route editor [B G1]
`moda.routes.RouteEditor` works on a node-structured model: a route = sorted id + nodes; a node = position (float32 bits) + its events, edge event first. Tables and offsets are rebuilt on save, so FRT-TABLE, FRT-EDGE-FIRST, FRT-ID-ORDER hold by construction; an unedited set saves byte-identically (vanilla tables are contiguous [D]).
Operations (each refuses at once with `EditError` when it would break an invariant):

- routes: `add_route(name|id, nodes)` (inserted in id order; duplicate id refused), `delete_route(r)`;
- nodes: `add_node(r, index, pos, edge=None, events=())` (edge default: copy of the neighbour's edge event), `move_node(r, index, pos)`, `delete_node(r, index)` (a route keeps at least one node);
- events: `add_event(r, node, index, event)` (index >= 1, isNodeEvent forced 1), `set_edge(r, node, event)` (isNodeEvent forced 0), `move_event(r, node, index, to_node, to_index)` (node events only), `delete_event(r, node, index)` (index >= 1; the edge event cannot be deleted);
- `save(path)` → validated writer; `to_routeset()`, `to_bytes()`.
Event spec (dict, JSON-safe): `type` (name → StrCode32, `"0x…"` or int), `time` (u16 frames, 60 / s, SoldierAI.md "Node waits"), `dir` (i16, × π/32768), `aimType`, `aim` (4 × u32), `params` (4 × u32), `isLoop`, `bodySection`, `pad` (hex of the 4 unused bytes, FRT.md). Missing keys are 0. `event_dict(raw)` is the inverse and is lossless.
`follow_table(route)` gives the route in the form `Engine\world\route_follow.step_after` takes: per node (position, [(type, time) of its node events]).

## JSON route form [B G1]
`{"format": "moda-frt-1", "version": 3, "routes": [{"id": "0x…", "name"?: …, "nodes": [{"pos": [x, y, z], "events": [edge, …]}]}]}`; float32 positions as JSON numbers (exact both ways), event specs as above with `name` added when the type is known. Export → import gives the same bytes.

## CLI [B G1]
`python Tools\moda <command>` (exit 1 when any error rule fires):

| Command | Does |
|---|---|
| `check <file>...` | all rules, one line per issue (`RULE sev where: text`) |
| `rewrite <in> <out>` | read with the codec, write through the validated writer |
| `route list <frt>` | route ids (names where known), node and event counts |
| `route export <frt> <out.json>` / `route import <in.json> <out.frt>` | JSON route form |
| `route apply <frt> <edits.json> <out.frt>` | edit script: list of `{"op": "add_node", "route": …, …}` with the editor's operation names and arguments, applied in order |

## Navmesh baker [B G2]
Code `Tools\moda\navbake.py` (bake), `Tools\moda\nav2mesh.py` (piece model + layout), `Tools\moda\nav2rules.py` (NAV2 rules). Format: [`docs\NAVMESH.md`](../formats/nav2.md); the path search it must serve: [`docs\engine\Navigation.md`](navigation.md). Verifier `Engine\tests\test_moda_baker.py`.

**Input = the walkable polygon surface** (JSON `moda-navsurface-1`, one per `.nav2` file): tile frame (`T`, `origin`, `quant` = header +0x44 x / y / z quanta per metre, `wsc` = +0x4A link units per metre, `magic`, `words` = header +0x4C..+0x5F) and pieces (0-3 border strips, 4 inner `_nav`, 5 inner `_nav.1`), each a list of polygons; **one polygon = one region**: `attr` (region attribute bits), `verts` (world metres) and `tris` (corner triples). This is the stage after voxelising and contouring: the collision geometry (`.geom`, [`docs\formats\GEOM.md`](../formats/geom.md)) is not used because its payloads are not decoded (E30) and this item does no RE. `surface_from_nav2` takes a vanilla file apart into exactly this input (the vanilla walkable polygons); everything else is recomputed.

**Vanilla build model [D, census 2026-11-06 over the 2,786 unique vanilla pieces].** The baker follows it; the percentage is how often the rule reproduces the stored value.

| Data | Rule | Census |
|---|---|---|
| Source vertices | absolute world positions on a **0.1 m grid in every axis**, float32 | every vertex |
| Vertex quanta | `floor((w - origin) * quant)`, float32 | 100 % |
| Triangle links | edge shared with another triangle of the piece: kind 0; of another piece of the tile: kind 1 (`0x4000 + tri`, ext1 = piece); of another tile: kind 2 `0xBFFF` (ext1 = piece, ext2 = T; files never store the far triangle, 18,475 / 18,475); else `0xFFFF`. Ext words only when a kind 1 / 2 link exists: ext1 `0xFFFF` on the other edges; ext2 `0xFFFF` on the other edges when a kind 2 link exists, else 0 | 99.5 % of baked triangles equal vanilla (the rest lie on the outer border of the baked set) |
| Kind-1 records | 16-byte rounded slots, straight after the poly-info table (4-byte aligned) | layout 2,786 / 2,786 |
| Edge nodes | per region, triangles in order, edges **1, 0, 2**: a new node for each region edge not seen yet; position `floor(((A + B) * 0.5 - origin) * quant)`, float32 | 100 % |
| Node flags / extras | bit 0 twin (same edge in another region of the piece, global node id), bit 1 piece link (piece, resolved node id), bit 2 tile link (T, piece, `0xFFFF`); kind bits 0 | 100 % |
| Node links | per region: triangles in order, pairs (0, 1), (0, 2), (1, 2) as (low, high), first one kept, stable-sorted by the low node | 2,802 / 2,802 regions |
| Link weight | `floor(wsc * length(midA - midB))`, float32 midpoints | 99.8 % (rest ±1) |
| Adjacency | per node: each triangle holding it (in order), that triangle's other two nodes in edge order; degree = 2 × triangles | 100 % |
| `node_tri` | last triangle of the region holding the node's edge | 100 % |
| Region box, tables | exact min / max of the region's vertices; starts cumulative | 100 % |
| Representative node | node nearest the area-weighted centroid of the region's triangles (3-D, metres) | 3,329 / 3,337 |
| Region links | one per neighbour: same piece (via twins), other piece (`piece`, region of the linked node), other tile (`T`, `piece`, region `0xFFF`, pad 0); ports = the region's nodes on that border, ascending; groups in that order, inside a group by port count descending, then lowest port | order 82 % / 99 % / 97 % |
| Region link cost | `floor(mean over ports of the in-region shortest path from the representative, in link weights)`; back = index of the reverse link in its own group | cost 88 % (rest ±2), back 100 % |
| Clusters (tail, class 0) | connected regions of equal attribute over same-piece and piece links (both files of a tile), numbered in first-encounter order (piece, region) | 102 / 120 tiles (the other 18 join `.1` pieces, which the census did not load) |
| Cluster node | the member region whose representative is nearest the cluster's area centroid; position = that representative, attr = its attribute | 496 / 496 |
| Cluster links | adjacent clusters, by cluster id, cost `floor(wsc * distance of the representatives)` | 428 / 428 |
| Classes 1, 2 | empty blocks (0x30 bytes); region cluster words `0xFFFF` | [D] |
| Grid | 13 × 13 cells of 10 m from the tile origin, y origin -32, word +0x28 1280; a cell lists per piece the regions whose x / z box touches it (closed intervals); y bytes = min / max box y >> 8; max y = max box y | 36,842 / 36,842 cells; y 99.6 % |
| Header | size `al16(0x64 + 36 × types)`, +0x14 first chunk id, +0x34 0x60, +0x38 `0x28 + 0x24 × (types - 1)`; chunks kind 0, 1, 4, 3 (types in order inside each kind), section table kinds 0, 3, 1; tail, then grid | [D] |

**Ours (not in the files, [?] in vanilla): border crossings of the cluster graph.** Vanilla pairs crossing *i* of a tile's border list with crossing *i* of the neighbour's opposite list, with unused `(0, 0xFFFF)` entries at the same places on both sides (one crossing per opening along the border, e.g. 5 openings + 4 unused on 140_138 / 140_137); how the original orders them is not recoverable. The baker makes one crossing per group of tile-link nodes joined across the border or inside the strip, ordered by the lowest world coordinate along the border (1 mm), computed from both sides so that two baked tiles agree; cost = mean shortest path (link weights over the whole tile, twins and piece links free) from the cluster's representative to the crossing's nodes. **Consequence: cluster links across a border pair correctly only between tiles baked in the same set.** A baked tile among vanilla neighbours keeps its mesh links (stitched by position at run time), but its cluster borders do not pair with theirs.
**Not baked:** off-mesh and run-time data (kind 3 triangle links, obstacle rings, dynamic links: run-time state, Navigation.md); the `extra` (mtbs) block.

`bake(surfaces)` bakes a set together (pieces and tiles link where border edges meet on the 0.1 m grid; an edge with no partner in the set is an open border) and returns the files in input order; the validated writer (`moda.write_bytes`) refuses any file that breaks a NAV2 error rule. Deterministic: same surfaces, same bytes. CLI: `python Tools\moda nav extract <surfaces.json> <file.nav2>...` (vanilla polygons out), `nav bake <surfaces.json> <outdir>` (every file through the validated writer, named after the surface `name`).

## NAV2 rules [B G2]
Registered with `moda.validate.register("nav2", ["nav2"], ...)`; `.nav2` entries of packages are checked as well (FPK-ENTRY). Every unique vanilla `.nav2` passes every rule (840 files, `test_moda_baker.py`). Dropped: a warning on node links of weight 0 (49 vanilla mtbs files have them).

| Rule | Sev | Check | Basis |
|---|---|---|---|
| NAV2-READ | error | magic `0x0C012B6A` / `0x0C012B69`, chunk prefixes and blocks inside the file | codec |
| NAV2-MODEL | error | container `serialize(read(b)) == b` | codec, 840 / 840 |
| NAV2-LAYOUT | error | every piece re-encodes from its decoded model to the same chunk bodies (offsets, alignment, slots, streams) | 2,786 / 2,786 [D] |
| NAV2-HEADER | error | chunk count = 4 × types, every type has kinds 0, 1, 3, 4, section table entries point at the kind 0 / 3 / 1 bodies, quanta and link units non-zero | [D] |
| NAV2-COUNTS | error | region starts cumulative and counts summing to the totals, polygons sorted by region, every polygon a triangle | [D] |
| NAV2-INDEX | error | corners, edge nodes, link ends, adjacency, twins, piece-link nodes, `node_tri`, region-link neighbours and ports inside their tables | [D] |
| NAV2-LINK | error | same-mesh triangle links are mutual; a link word of kind 1 / 2 has its ext words | [V 0x141CA4A90 reads them] |
| NAV2-NODE | error | a node lies within 8 quanta of its edge's midpoint | [D vanilla max 6.5 (mtbs), afgh / mafr ≤ 1] |
| NAV2-BOX | error | region box = min / max of its vertices | [D] |
| NAV2-REP | error | representative = one of the region's nodes | [D] |
| NAV2-BACK | error | back index of a same-mesh region link points at a link back to the region | [D] |
| NAV2-TAIL | error | class blocks inside the tail, region cluster ids below the cluster count (or `0xFFFF`), cluster representatives name existing regions and nodes | [D] |
| NAV2-GRID | error | listed piece ids exist in the file, listed regions below that piece's region count | [D] |

## Extension points
- New format: a module exposing `KIND`, `EXTENSIONS`, `codec` (read / write) and `check(raw) -> list[Issue]`, registered with `moda.validate.register(kind, extensions, checker)`; the writer and `check` pick it up by extension. G2 adds `.nav2` this way.
- Rules are data: severities live in `moda.validate.SEVERITY`, a caller may raise a warning to an error (`strict=` set); the vanilla event-type census is a JSON file regenerated by `python Tools\moda\census.py`.
- Classes registered by an engine mod (`TypeDB.register_from`, ModAPI.md "Extension kinds") pass FOX2-CLASS when the caller hands the writer that TypeDB (`typedb=`).
- Route edits are plain functions over the node model; an edit script op name maps to the editor method of the same name.
- Navmesh baker: the surface JSON is the interface. Any tool that produces walkable polygons on the 0.1 m grid (a voxeliser, a hand-made mesh, an edited vanilla surface) feeds `bake`; the NAV2 rules and the M8 oracle (`Engine\world\navigation.py`) check what comes out. The piece model (`moda.nav2mesh.Piece`) is the layer below for tools that edit derived data directly.

## Evidence
- G1 (`test_moda_toolkit.py`, 2026-11-06): all 307 unique vanilla `.frt` read → write byte-identical through the validated writer and clean under every rule; the JSON form round-trips them; broken files (one per error rule) are refused with that rule and leave no file; route edits on `f30010.frt` (add / move / delete node, add / move / delete event, add / delete route) keep every rule, load with `Engine\formats\frt.py`, and `route_follow.step_after` walks the edited route in the expected order (new node and its events visited, deleted node gone); edited `.frt` in a package passes the FPK writer and loads back; vanilla DataSets and packages pass their rules unedited.
- All 16,354 unique vanilla packages (8,247 fpk + 8,107 fpkd, every DataSet and `.frt` entry checked with its own rules, ~3 min, slow test `test_all_vanilla_packages_pass`): no error rule fires, no warning other than the dropped name rule below (2026-11-06 survey).
- Dropped rule: "every name hash resolves from the file's own string table" fired 242,812 times in vanilla. FOX2.md's 293,035 / 293,036 counts distinct hashes resolved by **some** file's table, not every file's (e.g. the empty-string value 0xB8A0BF169F98 is used without a table entry): not a per-file invariant.
- G2 (`test_moda_baker.py`, 2026-11-06): every unique vanilla piece (2,786 in 840 files) re-encodes byte-identically from its model; every vanilla `.nav2` passes every NAV2 rule; one broken file per error rule is refused with it and leaves no file; 3 × 3 blocks around 140_138 baked from their vanilla polygons give vanilla's vertices, nodes (all), edge-node numbering, node links and adjacency, `node_tri`, boxes, triangle links of the centre block (all), weights 99.8 % (rest ±1), representatives 99.9 %, region-link costs ≥ 75 % equal (rest ±2); baking is deterministic (also through JSON).
- **Gate (G2):** all 97 files of the 89 blocks the M8 jobs load, baked from their vanilla polygons (~25 s); every query runs through the M8 oracle on the vanilla and on the baked meshes. **1,297 of 1,348 within 0.1 m**: the 948 recorded M8 jobs (their loaded blocks, runtime bits, boxes and dynamic links) 938 (all 309 direct, all 614 finished searches, 15 of 25 coarse; the baked meshes also equal the live path on 938), seeded queries around 140_138 (seed 1, half under 80 m) 227 / 232 under 80 m and 132 / 168 longer. Swapping vanilla's region links and tail into the baked files gives 400 / 400 seeded queries: the remaining misses come from the region-link costs (88 % exact) and order and from our cluster border crossings, not from the triangle mesh.
- Build model census (2026-11-06, [`docs\NAVMESH.md`](../formats/nav2.md) "Build model"): the rules and rates in "Navmesh baker".
- Vanilla `.frt` invariants (2026-11-06 census over 307 files, 104,653 routes, 963,624 events): ids sorted and unique, every route with a node, every node with its edge event, contiguous tables using every event once, edge-then-node order, finite positions, bodySection 0, isLoop 0 / 1 (1,393 loops) [D].

## Open
- G3 mod-Lua harness (needs one live capture of 10 seeded broken modules), G4 live check of an edited route and a baked navmesh in the game.
- Baker [?]: vanilla's border-crossing order (so a single baked tile pairs with vanilla neighbours; until then bake the neighbours too); region-link cost (12 % off by 1-2: the original's path costs are not the stored weights') and order (18 % of same-piece lists); polygons from collision geometry (`.geom` payloads, E30) or a voxeliser of our own; off-mesh links. G4 decides whether the game accepts our crossings and header words +0x4C..+0x5F copied from the replaced tile.
- Aim words of `ROUTE_AS_*` aim types name other routes; not checked against the set (routes of other sets are allowed) [?].
- The exe's behaviour for an unknown event type (ignored or fault) is not read; FRT-TYPE stays a warning until G4 [?].

---
<small>Source: `docs/engine/ModToolkit.md` in the project repository &middot; generated 2026-11-06.</small>
