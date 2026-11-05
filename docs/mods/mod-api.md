# Writing a mod for the new engine

*M10 Mod API core, IN PROGRESS (2026-11-05): all 14 gate checks pass, the gate awaits Luc's review. API version 0.1. The engine's repository is private for now, so nobody outside the project can run these mods yet. The code below uses the real API: it mirrors the nine reference mods the engine's tests load and check. Background: [How mods plug into the engine](../explain/mod-api.md). Exact details: [Mod API](../engine/mod-api.md).*

## Python or Lua
| | Python mod | Lua mod |
|---|---|---|
| For | prototypes you write or have read yourself | mods meant for sharing |
| Runs | inside the engine process, full access | in its own Lua 5.1 sandbox |
| Can do | every extension kind | parameters, tables, own messages, Lua libraries, hooks |
| Cannot | (no limits: that is the risk) | files, OS, clock, `require`, precompiled code, more than 10 million instructions per call |

Never load a Python mod from someone you do not trust: it can do anything your user account can.

## The manifest
A Lua mod is a folder with `mod.json` and its entry file:

```json
{"namespace": "lualib", "version": "1.0.0", "api": "0.1", "kind": "lua",
 "entry": "main.lua", "depends": ["vanilla"]}
```

- `namespace`: lower case, 2 to 32 characters, unique. `vanilla` and `engine` are reserved. **Every new name your mod registers must start with it** (`lualib.Greeting`, `morale.MoraleSystem`).
- `api`: during 0.x it must equal the engine's version exactly; a mismatch is refused with both versions in the message.
- `depends`: mods that must be loaded (missing one refuses your mod). `after` / `before`: order hints that are ignored when the other mod is absent.

A Python mod gives the same fields as a `Manifest(...)` and a `register(ctx)` function.

## What a mod can do
Each row is one extension kind, with the reference mod that tests it.

| You want to | Call | Reference mod |
|---|---|---|
| Add a system that runs every frame | `ctx.register("updaters", "ns.Name", {"priority": p}, impl=factory)` | `morale` |
| React to a message, or raise your own | `ctx.listen("Finish", fn)`, `ctx.message("ns.Rally")` | `listener` |
| Add a game object type and its commands | `ctx.register("gameobject_types", 120, ...)`, `ctx.register("commands", "120:ns.SetLevel", ..., impl=fn)` | `beacon` |
| Wrap an existing command handler | `ctx.override("commands", key, impl=fn)` with `fn(next, instance, args)` | `chain` |
| Add a DataSet class | `ctx.register("reflection_classes", "ns.Beacon", {"super": "Data", "properties": [...]})` | `fox2cls` |
| Change a measured value | `ctx.override("parameters", "cp.rate.alert", value=...)` | `alertrate` |
| Watch, change or stop an engine call | `ctx.hook(site, before=fn, after=fn)` | `holdroute`, `chain`, `morale` |
| Add or rename soldier AI table entries | `ctx.override("ai_tables", name, value=...)` | `ainode` |
| Give the game's Lua a new library | Lua: `mod.library("ns.Lib", {Fn = function ... end})` | `lualib` |

## Hooks in practice
A before hook gets a `call` with `args` (changeable), `view` (a read-only snapshot) and `frame`. It may change `args`, return `CANCEL`, or return nothing. An after hook gets the result and returns the result passed on.

```python
from Engine.mods import hooks

def register(ctx):
    def before(call):
        if call.args["soldier"] == 91:      # keep soldier 91 on its current leg
            return hooks.CANCEL
    ctx.hook("route.switch", before=before)
```

In Lua the same idea:

```lua
mod.hook("cp.phase_change", function(args, view)
  if args.to_phase == 3 then return mod.CANCEL end   -- this base never goes to alert
end, nil)
```

## How this would be used in a mod
*Hypothetical and untested as a whole: each piece is one of the tested reference mods, but this combination was never built or run.* A "jittery garrison" mod: bases in alert drain their timer 1.5 times faster (parameter override, as `alertrate`), a morale system lowers morale every frame a base spends in alert or evasion (updater plus a `cp.phase_change` hook, as `morale`), and once morale reaches 0 a before hook on `route.switch` keeps that base's soldiers in place, as if they refused to patrol (as `holdroute`). Because the engine is deterministic, the mod's author can state the effect exactly before anyone plays: with the alert rate change alone, the recorded alert at the Soviet base ends after 1,199 frames instead of 1,798, and nothing else in the trace moves.

## Check your mod like the engine checks its own
The engine's reference mods pass three checks before they count; a mod of your own should pass the same ones:

1. **Empty-mod baseline.** Run your scenario with only vanilla loaded and keep the trace. Every difference your mod makes is measured against it.
2. **Prediction.** Write down what should change before you run it, as the reference mods do: `alertrate` predicts 1,199 frames from the arithmetic alone, `holdroute` predicts that exactly one soldier's switches change.
3. **Double run.** Run the same mods with the same seed twice in fresh engine instances (the engine's `double_run` helper does this): the owner-tagged trace must be byte-identical. The engine's own check (C4) also repeats each scenario in a fresh process with a different hash seed, which catches code whose result depends on the iteration order of a Python `set` or `dict` of hashed keys.

If your mod's numbers come from a recording of the real game, keep at least two recordings that agree, or write down which values differ and why: the same rule the engine's fixtures follow (C5).

## Benefits
- **Errors name the culprit.** Name clashes, hash collisions, missing dependencies, load-order cycles, version mismatches and sandbox escapes are refused with the mod(s) named, and the whole set is undone.
- **Order is documented.** The last loaded override wins; before hooks run in load order, after hooks in reverse. The same mods give the same result every run, whatever order you list them in.
- **Effects are testable offline.** Load your mod into an engine instance, run a recorded scenario and compare with vanilla. Other instances (and the engine's built-in vanilla defaults) are not affected.
- **Your mod can be checked for determinism**: a double run with the same seed must give byte-identical output.

## Pitfalls
- **Build tables from the current value, not the vanilla one.** Read with `ctx.get(...)`, change, then override. If you copy the vanilla constant, you silently drop what mods loaded before you added.
- **Use the mod's random generator** (`ctx.random`, Lua `math.random`). Python's `random` or the clock make the double run fail.
- **Never let a set decide an order.** Iterating a Python `set` (or sorting with ties left to it) can change between processes; sort by a key that breaks every tie. The engine itself had one such bug, found by its determinism check.
- **Float values**: rates are 32-bit floats. Give a value that rounds as you expect, or the bit pattern too.
- **Message names are hashed to 32 bits.** A refused collision means: rename your message.
- **A chained handler needs a previous one.** Vanilla's 514 command handlers are registered as names only; `next` fails on them until their milestone ports them.
- **Cancelling is blunt.** A cancelled phase change keeps the phase but leaves the timer as it is; a cancelled route switch leaves the soldier on its record.
- **Hook views are snapshots.** Changing them does nothing; change `args` or the result.

## Limitations (today)
- Headless engine: no graphics, sound or input yet (M20 to M22). Mods change a simulation, not a game you can play.
- Three hook sites (`route.switch`, `cp.phase_change`, `command.dispatch`); more come with each milestone's extension points.
- API 0.1: breaking changes until 1.0 (M24).
- Python and Lua only: native plugins come with M24 and will need a reference version plus a bit-identical test, the rule the engine's own [C++ backend](../explain/native-backend.md) follows.
- Mods for this engine do not run in the original game. For the original game see the other guides; tools whose output goes into the original game are the MOD-A track (in scope since 2026-11-05, next after M10).

---
<small>Hand-written article (`docs/site/mods/Mod-API.md`) &middot; published 2026-11-05.</small>
