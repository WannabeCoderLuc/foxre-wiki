# Mod API

Clean-room engine design for M10 ([`docs\ROADMAP.md`](../status/roadmap.md) M10, standing rules "Data-driven registries", "Determinism", "Compat mode").
Module `Engine\mods\`. API version **0.1** (0.x until M24 freezes 1.0). No new RE: this sits on M2-M9.
Tags: [B] built and tested (gate item named), [P] planned (gate item named), [D] design decision.

## Principles [D]
- **Vanilla is a mod.** Everything the engine knows about the original game is registered by the `vanilla` mod (`Engine\mods\vanilla\`) through the same `ModContext` calls a mod uses. Its manifest is fixed: namespace `vanilla`, load position 0, no dependencies.
- **Registries own the tables.** Engine modules read GameObject types, command handlers, message ids, updaters, AI tables, resource loaders, reflection classes, Lua libraries, natives and parameters from a `Registries` instance, not from module-level dicts. Module constants that carry measured values (`cp_phase.RATE`, `route_follow.STEP_NAMES` ...) stay as the vanilla mod's *source*; the registry is what consumers and mods see.
- **One `Registries` per engine instance**, never global: two hosts in one process (tests, double runs for C4) share nothing.
- **Compat mode:** with only `vanilla` loaded every M0-M9 gate passes unchanged (G1); with the null mod loaded traces are byte-identical (G2).
- **Determinism:** registration order is a pure function of the resolved load order; registries iterate in registration order; dumps are canonical JSON. No registry call reads time, randomness or the filesystem order.

## Registries [B G1]
`Engine\mods\registry.py`. Each kind is a `Registry` with entries `Entry(key, value, owner, impl, layers)`:

- `key`: the canonical key of the kind (below); `value`: JSON-able descriptor (what the dump shows); `impl`: optional Python callable / factory (not dumped); `owner`: namespace of the mod that registered it; `layers`: `(owner, value)` history of overrides, in load order.
- `register(key, value, impl=None)` adds a key; a key already present raises `Conflict` naming both owners.
- `override(key, value=..., impl=...)` replaces an existing entry's value and / or impl and appends a layer; the last loaded mod wins (G5 pins the order).
- Iteration (`items()`, `keys()`) is registration order. `dump()` = `{key: value}` in that order; `Registries.dump_json()` = canonical JSON of every kind (sorted keys inside values, kinds in fixed order).

| Kind | Key | Value (dumped) | Consumer today | Vanilla source |
|---|---|---|---|---|
| `gameobject_types` | type index (int, 0-127) | `{name, group}` | `GameObjectManager.register_from` (types with a manager factory) | `vanilla/gameobject_types.json` (type index table 0x142A7BA90, update groups of `m3_frame_trace.json`) |
| `commands` | `"<handler>:<Command>"` (vanilla: handler function VA; engine / mod types: the type index) | `{handler, owner, name, hash32}` | `TypeManager.command` default dispatch (`handlers`) | `vanilla/commands.json` (knowledge DB `cmd_handlers.tsv`) |
| `messages` | StrCode32 id (int) | `{name, category, module}` | collision check for mod ids; bus routes by id | constants of `Engine\runtime\*`, M3 frame-trace messages |
| `updaters` | updater name (str) | `{priority, vtable, update}` | `UpdateService.register_from` (updaters with a factory) | `vanilla/updaters.json` (M3 live updater vector) |
| `ai_tables` | table name (str) | table as JSON | `route_follow`, `cp_phase`, `realize` (vanilla source today) | module constants of `Engine\world\` |
| `parameters` | dotted name (str) | `{value, type, bits?}` | `Registries.param(name)`; override target of G3 / G5 | `cp_phase` rates, realize budget / margins |
| `resource_loaders` | file extension (str) | `{type_id, codec}` | `Registries.codec_for(path)` | `pathcode.EXTENSIONS` + `Engine\formats\` / `Engine\resources\` codecs |
| `reflection_classes` | class name (str) | `{super, version, hash}` | `TypeDB` (vanilla source) | `fox_edb.json` via `Engine\core\typedb.py` |
| `lua_libraries` | library name (str) | `{kind, after_chunks, members, values}` | `ScriptHost.register_upto` | `m4_lua_bindings.json` |
| `natives` | `"Lib.Func"` | `{owner_module}` | `ScriptHost.natives` (a live view of this registry) | `ScriptHost` sources (loader, timers, popups, title, stage blocks ...) + recorded answers |

Not every vanilla entry has an implementation: GameObject types, command handlers and updaters are registered as **descriptors** (name, id, priority) so ids are reserved and collisions are caught, and get an `impl` when the owning milestone ports them (`commands_owner.json`, `natives_owner.json`, G7).

## Manifest [B G1 basic checks, P G4 full rejections]
`mod.json` (or a `MANIFEST` dict in a Python mod):
```json
{"namespace": "morale", "version": "0.1.0", "api": "0.1", "kind": "python",
 "entry": "morale.py", "depends": ["vanilla"], "after": [], "before": []}
```

- `namespace`: `[a-z][a-z0-9_]{1,31}`, unique; `vanilla` and `engine` reserved.
- `api`: `major.minor` of the Mod API it was written for; accepted when major equals and minor <= the engine's (0.x: minor must be equal, no compatibility promise before 1.0).
- `kind`: `python` (prototype mods, trusted, same process) or `lua` (sandboxed, below).
- `depends`: hard dependencies (missing -> refused); `after` / `before`: soft order constraints.

## Loader [B G1 order, P G4 / G5]
`Engine\mods\loader.py`, `ModLoader(registries).load(mods)`:

1. Validate every manifest (namespace, API version, entry).
2. Resolve order: `vanilla` first; then a topological sort over `depends` + `after` + `before`, ties broken by namespace (stable, independent of the filesystem). Missing dependency or a cycle refuses the whole set with a precise error.
3. For each mod in order: build a `ModContext(registries, manifest)` and call the mod's `register(ctx)`.
4. Conflicts: registering a key that exists raises `Conflict` (owner of the existing entry and the new one named). New string keys of non-vanilla mods must be namespaced (`<ns>.Name`, message names hashed as StrCode32 of `"<ns>.Name"`); a new message id equal to an existing one is a collision (G4).
5. `ModLoader.order` and `Registries.dump_json()` are the load report.

## Extension kinds [P G3 reference mods, one each]
| Kind | API | Engine hook point |
|---|---|---|
| New system | `ctx.register("updaters", "<ns>.Name", {priority}, impl=factory)` with lifecycle `OnAllocate / OnInitialize / OnUpdate / OnTerminate` | `UpdateService` vector (priority order, insertion sort, `Scheduler.md`) |
| Message listener / own message ids | `ctx.listen(name_or_id, fn)`, `ctx.register("messages", strcode32("<ns>.Name"), {...})` | `MessageBus.add_listener` (`Messages.md`) |
| New GameObject type + SendCommand handlers | `ctx.register("gameobject_types", index, {...}, impl=manager_factory)`; `ctx.register("commands", "<type>:<ns>.Cmd", ..., impl=fn)` | `GameObjectManager.register_from`, `TypeManager.command` |
| New `.fox2` class | `ctx.register("reflection_classes", "<Ns>Class", {...})` | `TypeDB` lookup / entity build (`Entities.md`) |
| Parameter override | `ctx.override("parameters", name, value)`; layered by load order | `Registries.param` |
| Before / after hooks | `ctx.hook(target, before=fn, after=fn)`; a before hook may change the arguments or cancel | named hook sites in engine modules (route switch, phase change, command dispatch) |
| SendCommand handler chaining | `ctx.override("commands", key, impl=fn)`, `fn(next, instance, args)` calls the previous handler | command dispatch |
| AI node insert / replace | `ctx.override("ai_tables", "route.steps", ...)` | step / role tables (`SoldierAI.md`) |
| Blackboard access | read-only views of CP / soldier state passed to hooks | `cp_phase`, `route_follow` records |
| Lua library | `ctx.register("lua_libraries", "<Ns>Lib", {kind, after_chunks, members})` + `natives` | `ScriptHost.register_upto` |

## Sandbox (Lua mods) [P G4]
Lua mods run in the M4 host's Lua 5.1 with the `lua51_run` pattern: a fresh environment table per mod containing only `string`, `table`, `math` (with `math.random` replaced by the engine's seeded generator), `pairs`, `ipairs`, `type`, `tostring`, `tonumber`, `select`, `error`, `pcall`, `setmetatable` / `getmetatable` (no `__gc`), and the mod's own API table. Refused: `os`, `io`, `debug`, `require`, `package`, `loadfile`, `dofile`, `load` / `loadstring` of binary chunks (first byte `\27`), `collectgarbage`, `rawset` on engine tables. Instruction-count hook bounds each call.

## Determinism [D, P C4 / G4]
- Randomness only from the engine's seeded generator (the game's own generator from M13); mods get it through the context, never `random` / `math.random` directly.
- No wall clock: mods see the frame counter and the host clock (1/60 s per frame).
- Registration order, iteration order and dump order follow the resolved load order; no hash-set iteration anywhere in the registry.
- G4 catches nondeterminism by a double run with the same seed (byte-identical traces).

## Extension points
This document is the extension-point index; each subsystem spec names its own:

- `Scheduler.md`: updaters (priority, lifecycle), GameObject type slots and update groups.
- `Messages.md`: message ids (namespaced StrCode32), listeners, SendCommand handlers and chaining.
- `Entities.md` / `Reflection.md`: reflection classes, `.fox2` classes from mod DataSets.
- `ScriptHost.md`: Lua libraries, natives, Lua mod sandbox.
- `Resources.md`: resource loaders by extension, packages from mods.
- `World.md`: stage-block and identifier data from mods.
- `Navigation.md`: nav worlds and path queries (MOD-D).
- `SoldierAI.md`: phase rates, radio types, member roles, route step table, realize budget.

## Evidence
- Vanilla tables registered from: `Engine\tests\fixtures\m4_lua_bindings.json` (Lua libraries), `m3_frame_trace.json` (updater vector, type update groups), `mgsv_unified_server\data\re\gameobject_type_index.tsv` and `cmd_handlers.tsv` (copied into `Engine\mods\vanilla\*.json`), `fox_edb.json` (reflection), constants of `Engine\runtime\*` and `Engine\world\*`.
- `Engine\tests\test_m10_registry.py` (G1): every registry dump equals the table it came from; two builds give byte-identical dumps; the script host installs Lua libraries and natives only through the registry; M0-M9 gate test files unchanged against `verifiers.lock.json`.

## Open
- Hook sites (G3): which engine functions expose before / after hooks, and the blackboard view types.
- Lua mod sandbox and the instruction budget value (G4).
- Overhead budget (G6): registry lookups are dict lookups at registration time; per-frame dispatch is unchanged until hooks exist.

---
<small>Source: `docs/engine/ModAPI.md` in the project repository &middot; generated 2026-11-04.</small>
