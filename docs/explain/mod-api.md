# How mods plug into the engine

*M10 Mod API core, PASS (accepted 2026-11-05): all 14 gate checks pass (items G1 to G7 and the common checks C1, C2, C4 to C8; C3 does not apply to M10). API version 0.1. Exact details: [Mod API](../engine/mod-api.md). How to write one: [Writing a mod for the new engine](../mods/mod-api.md).*

## What it is
The Mod API is the documented way for a mod to add to the new engine or change it, without editing the engine's code. A mod is a small package with a **manifest** (its name, the API version it was written for, what must load before it) and a **register** step that tells the engine what it adds or changes.

Everything a mod can touch lives in **registries**: tables of named entries that the engine reads instead of values written into its code. There are ten kinds of tables for what the engine already runs, and two more for what mods attach to it:

| Registry | Holds | From the original game |
|---|---|---|
| Game object types | the 128 object type slots and their update group | 92 types: soldier, vehicle, heli ... |
| Commands | `SendCommand` handlers per type | 514 handlers: `SetPhase`, `SwitchRoute` ... |
| Messages | 32-bit message ids and their names | 28, for example `Finish` from a timer |
| Updaters | systems that run once per frame, by priority | the 24 per-frame updaters |
| AI tables | soldier and base tables | 8: route step names, events that run without stopping ... |
| Parameters | measured constants | 9: alert drain rate 1/30 per second, the far-mode budget ... |
| Resource loaders | file extension to reader | 140: `.fox2`, `.frt`, `.nav2` ... |
| Reflection classes | DataSet classes and their properties | the 1,153 classes of the game |
| Lua libraries | the libraries the game's Lua sees | 399 |
| Natives | the functions inside those libraries that the engine answers | about 109 per script host, out of 5,532 bindings |
| Hooks | before / after functions at named engine calls | none (the game has no such thing) |
| Listeners | mod functions called when a message is raised | none |

The original game's content is registered by a built-in mod called **vanilla**, through exactly the same calls a mod uses. A mod is never a second-class citizen: it sits in the same tables, in a documented order, and every entry records which mod put it there.

## Why it matters
The project wants an engine other people can build on, not only a faithful copy. Opening the engine up while it still has few systems (right after M9) keeps every later system honest: from M11 on, each new system has to say in its specification what a mod may register, override, hook or replace, and the milestone ships a reference mod for each new extension point.

For the project itself the API is also a testing tool. Because every measured value sits in a registry, a test can change one value and check that the engine's output moves by exactly the predicted amount, and that nothing else moves.

## How the original does it
The original game has no mod API. It does have internal registries (the class registry, the object type table, the Lua library registration), but the executable fills them at start-up and nothing outside it can add to them. Modding the original means one of:

- **Replacing files** inside the game's archives (SnakeBite installs packages).
- **Overriding Lua**: the game's scripts are plain Lua 5.1, so a mod can wrap or replace script functions (Infinite Heaven works this way).
- **Hooking native code** at fixed addresses (IHHook plugins), which only works for one build of the executable.

All three work, but conflicts are silent (two mods replacing the same file or function: the last one wins and nobody is told), and the only test is to play.

## How our engine does it
1. **Manifest check.** Namespace (lower case, unique; `vanilla` and `engine` are reserved), API version (during 0.x the minor version must match exactly), kind (Python or Lua), dependencies. Every new name a mod registers must start with its namespace.
2. **Load order.** Vanilla first. Then every mod after the mods it `depends` on, and after or before the mods its `after` / `before` hints name (hints about absent mods are ignored). When nothing decides, the mod with the alphabetically smaller namespace goes first. The order is a pure function of the set of mods: neither the folder listing, nor the order you list them in, nor the run changes it. A second batch of mods loaded later comes after the first.
3. **Registration.** Each mod's register step runs with a context bound to its namespace. Every change is journaled. If any mod in the set is refused, the whole set is undone, the registries are exactly as before, and the error names the mod.
4. **Overrides.** When several mods override one value, the last loaded wins, and the full history of who changed it is kept. Chained command handlers wrap each other the same way: the last loaded is outermost.
5. **Hook sites.** At three named engine calls, mods may watch, change or stop the call:

| Site | Engine call | Cancelling means |
|---|---|---|
| `route.switch` | a soldier moves to the next leg or node event of its route | the soldier stays on its current leg or event |
| `cp.phase_change` | a base (command post) changes phase | the base keeps its phase |
| `command.dispatch` | a `SendCommand` reaches its handler | the handler is not called |

Before hooks run in load order and may change the call's arguments; one that cancels stops the later ones and the call itself. After hooks run in reverse order (the first loaded mod wraps the outside), all of them, even after a cancel. Hooks see read-only snapshots of the base, the soldier or the player, never the engine's live objects. A site with no hooks costs one table lookup.

6. **Lua sandbox.** Lua mods run in their own Lua 5.1 state: no files, no operating system, no clock, no `require`, no debug library, no precompiled code, and at most 10 million Lua instructions per call. Random numbers come from the mod's own seeded generator. Python mods are trusted and not sandboxed: they are for your own prototypes.

## Nine reference mods
Each kind of extension has a small mod in the engine's tests that uses it, with a fixture and a prediction made independently of the engine:

| Mod | Uses | Checked result |
|---|---|---|
| morale | a new per-frame system plus a phase-change hook | final morale equals the value computed by hand from the recorded phases |
| listener | a message listener and its own message id | raises its own message in the same delivery round as the timer's `Finish` |
| beacon | a new game object type with commands | the object ticks and answers its commands |
| chain | wraps a command handler, hooks every command | both layers apply: the level is clamped and negative values are rewritten |
| fox2cls | a new DataSet class | its three objects load and are typed only when the class is registered |
| alertrate | a parameter override (alert rate 1/20 instead of 1/30) | the recorded alert drains in 1,199 frames instead of 1,798; caution and evasion unchanged |
| holdroute | a route-switch hook that cancels | soldier 91 stays on all 52 of its switches; the other 1,627 equal vanilla |
| ainode | an AI table insert | a soldier's step differs from vanilla exactly where vanilla lands on the inserted event |
| lualib | a Lua library and a Lua hook, in the sandbox | the game's Lua calls the library; a function that reads `os` is refused |

## Determinism: the same run twice
A mod's effect only means something if it can be replayed. The engine promises: randomness only from seeded generators, no wall clock, fixed iteration orders. The common check **C4** tests that promise on every M10 scenario (24 in all: the empty mod on the frame loop, script host and soldier scenarios; the nine reference mods with hooks at all three sites; the load-order cases forward and reversed). Each runs twice in fresh engine instances and once more in a fresh Python process with a different hash seed; the result, the owner-tagged trace and the registry dump must be byte-identical. Two controls prove the check can fail: a mod drawing different random numbers with seed 0 and seed 1 is caught, and so is a mod that keeps hidden state between runs.

The check found one real problem: a coverage report broke ties between equally often called functions by Python's set order, which changes with the hash seed. Ties are now sorted by name.

## Where the test data comes from
The tests compare the engine with recordings of the real game (fixtures). The common check **C5** makes sure each fixture an M10 test reads is trustworthy: 18 fixtures are listed with where they came from. A live fixture must come from run folders that exist and are named by the fixture or its specification, from at least two runs that agree; where values differ between runs (for example the clock), the specification says which run is used and why. Derived fixtures name the tool and the inputs that made them. Writing this down found gaps in the documentation (run names only in the session log; varying values, single-read save images and a single path capture without a stated reason in the specification); they were documented, no run was invented and no fixture changed.

## Benefits
- **Conflicts are found, not hidden.** Two mods registering the same name, or two message names that hash to the same 32-bit id, are refused with both mods named. The project found real colliding names by brute force and uses them in the tests.
- **Predictable effects.** A change can be checked before anyone plays: the alert rate example above is exact arithmetic, not an estimate.
- **Replayable.** The same mods and the same seed give byte-identical results; a mod that reads the clock or unseeded random numbers is caught by a double run.
- **Nothing changes by accident.** With an empty mod loaded, every earlier test passes byte for byte. With only vanilla loaded, the engine behaves exactly like before M10.
- **Cheap.** Reading values through the registries costs at most about 3 % frame time against the old hardcoded path (measured 0.5 to 1.8 % on the soldier scenarios, 0.9 to 3.2 % on the frame-loop scenario; the budget is 5 %).
- **Every native has an owner.** All 5,532 Lua natives and all 514 command handlers name the milestone that must implement them, so a mod author can see when a system will be real.

## Pitfalls and limitations
- **The engine is not a game yet.** It runs headless: no graphics, sound or input until M20 to M22. A mod today changes a simulation that tests compare with the real game, nothing you can play.
- **Private for now.** The engine's repository is private; the API is documented here so it can be discussed and published later.
- **API 0.x is not stable.** Until M24 freezes version 1.0, a mod written for 0.1 is refused by 0.2. Expect breaking changes.
- **Few hook sites.** Three so far. The caution / evasion route switch is not ported yet, so it is not part of `route.switch`.
- **Most handlers are names only.** All 514 vanilla command handlers are registered so their names are reserved, but none is implemented yet; chaining onto one fails until its milestone ports it.
- **Natives are mostly recorded.** The game's Lua still gets many answers replayed from a recorded session; a mod cannot call game systems that do not exist in the engine yet.
- **Cancelling is blunt.** A cancelled phase change keeps the old phase but leaves the timer alone; a cancelled route switch leaves the soldier where it is until something else moves it.
- **Hooks cost what they do.** The 5 % budget covers the API with no hooks; a hooked site costs what its hooks cost.
- **Python mods are not sandboxed.** Never load one you have not read.
- **No native code in mods yet.** Mods are Python or Lua; native plugins come with M24 and must pass the same bit-identical test as the engine's own [C++ backend](native-backend.md).
- **One open question:** the order of a mod listener relative to the mission script's own update (E45).

## How we know
- `test_m10_registry.py`, `test_m10_consumers.py`: every registry equals the table it came from, two builds give identical dumps, engine code reads its values through the registry.
- `test_m10_null_mod.py`: an empty mod changes nothing in the M3, M4 and M9 scenarios.
- `test_m10_ref_mods.py`: the nine reference mods, each against a fixture and an independent prediction.
- `test_m10_rejects.py`: every refusal with a real case, including genuine hash collisions.
- `test_m10_load_order.py`: two mods on one value or one hook site resolve the same way for every input order and every run.
- `test_m10_perf.py`: the 5 % frame-time budget.
- `test_natives_owned.py`: every native and every command handler has the milestone that must implement it.
- `test_determinism.py` (C4), `test_fixture_provenance.py` (C5), `test_cpp_equiv.py` (C7), `test_site_build.py` (C8), and the whole test suite (C1).

---
<small>Hand-written article (`docs/site/explain/Mod-API.md`) &middot; published 2026-11-06.</small>
