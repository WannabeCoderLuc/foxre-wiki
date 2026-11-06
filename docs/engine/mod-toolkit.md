# Mod toolkit (MOD-A)

Code `Tools\moda\` (Python: tools stay Python by rule; no engine code). Verifier `Engine\tests\test_moda_toolkit.py`. Gate: [`docs\ROADMAP.md`](../status/roadmap.md) "Mod track", MOD-A G1-G4 (`gates.json` "MOD", items `MOD-A.G1` …).
Tags: [B Gk] built and checked by gate item k, [D] holds in every vanilla file, [V] exe / verified elsewhere (cited), [I], [?].
**State (2026-11-06):** G1 built (validated writers + `.frt` route editor). G2 navmesh baker, G3 mod-Lua harness, G4 live: not built.

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

## Extension points
- New format: a module exposing `KIND`, `EXTENSIONS`, `codec` (read / write) and `check(raw) -> list[Issue]`, registered with `moda.validate.register(kind, extensions, checker)`; the writer and `check` pick it up by extension. G2 adds `.nav2` this way.
- Rules are data: severities live in `moda.validate.SEVERITY`, a caller may raise a warning to an error (`strict=` set); the vanilla event-type census is a JSON file regenerated by `python Tools\moda\census.py`.
- Classes registered by an engine mod (`TypeDB.register_from`, ModAPI.md "Extension kinds") pass FOX2-CLASS when the caller hands the writer that TypeDB (`typedb=`).
- Route edits are plain functions over the node model; an edit script op name maps to the editor method of the same name.

## Evidence
- G1 (`test_moda_toolkit.py`, 2026-11-06): all 307 unique vanilla `.frt` read → write byte-identical through the validated writer and clean under every rule; the JSON form round-trips them; broken files (one per error rule) are refused with that rule and leave no file; route edits on `f30010.frt` (add / move / delete node, add / move / delete event, add / delete route) keep every rule, load with `Engine\formats\frt.py`, and `route_follow.step_after` walks the edited route in the expected order (new node and its events visited, deleted node gone); edited `.frt` in a package passes the FPK writer and loads back; vanilla DataSets and packages pass their rules unedited.
- All 16,354 unique vanilla packages (8,247 fpk + 8,107 fpkd, every DataSet and `.frt` entry checked with its own rules, ~3 min, slow test `test_all_vanilla_packages_pass`): no error rule fires, no warning other than the dropped name rule below (2026-11-06 survey).
- Dropped rule: "every name hash resolves from the file's own string table" fired 242,812 times in vanilla. FOX2.md's 293,035 / 293,036 counts distinct hashes resolved by **some** file's table, not every file's (e.g. the empty-string value 0xB8A0BF169F98 is used without a table entry): not a per-file invariant.
- Vanilla `.frt` invariants (2026-11-06 census over 307 files, 104,653 routes, 963,624 events): ids sorted and unique, every route with a node, every node with its edge event, contiguous tables using every event once, edge-then-node order, finite positions, bodySection 0, isLoop 0 / 1 (1,393 loops) [D].

## Open
- G2 navmesh baker, G3 mod-Lua harness (needs one live capture of 10 seeded broken modules), G4 live check of an edited route and a baked navmesh in the game.
- Aim words of `ROUTE_AS_*` aim types name other routes; not checked against the set (routes of other sets are allowed) [?].
- The exe's behaviour for an unknown event type (ignored or fault) is not read; FRT-TYPE stays a warning until G4 [?].

---
<small>Source: `docs/engine/ModToolkit.md` in the project repository &middot; generated 2026-11-06.</small>
