# How mods plug into the engine

*M10 Mod API core, IN PROGRESS (2026-11-05): gate items G1 to G7 pass; the common checks for determinism (C4), fixture provenance (C5), the C++ backend (C7) and the site build (C8) are still open, and Luc has not accepted the gate yet. Exact details: [Mod API](../engine/mod-api.md). How to write one: [Writing a mod for the new engine](../mods/mod-api.md).*

## What it is
The Mod API is the documented way for a mod to add to the new engine or change it, without editing the engine's code. A mod is a small package with a **manifest** (its name, the API version it was written for, what it needs loaded first) and a **register** step that tells the engine what it adds.

Everything a mod can touch lives in **registries**: tables of named entries the engine reads instead of hardcoded values. There are 12 kinds:

| Registry | Holds | Example from the original game |
|---|---|---|
| Game object types | the 128 object type slots and their update group | soldier, vehicle, heli |
| Commands | `SendCommand` handlers per type | `SetPhase`, `SwitchRoute` |
| Messages | 32-bit message ids and their names | `Finish` from a timer |
| Updaters | systems that run once per frame, by priority | the 24 per-frame updaters of the real game |
| AI tables | soldier and base tables | route step names, events that run without stopping |
| Parameters | measured constants | alert drain rate 1/30 per second |
| Resource loaders | file extension to reader | `.fox2`, `.frt`, `.nav2` |
| Reflection classes | DataSet classes and their properties | the 1,153 classes of the game |
| Lua libraries and natives | what the game's Lua can call | the 5,532 native functions |
| Hooks | before / after functions at named engine calls | none in the original |
| Listeners | mod functions called when a message is raised | none in the original |

The original game's own content is registered by a built-in mod called **vanilla**, through exactly the same calls a mod uses. A mod is never a second-class citizen: it sits in the same tables, in a documented order.

## Why it matters
The project wants an engine other people can build on, not only a faithful copy. Opening the engine up while it still has few systems (right after M9) keeps every later system honest: from M11 on, each new subsystem has to say in its spec what a mod may register, override, hook or replace.

For the project itself the API is also a testing tool. Because every measured value sits in a registry, a test can change one value and check that the engine's output moves by exactly the predicted amount, and nothing else moves.

## How the original does it
The original game has no mod API. It does have internal registries (the class registry, the type table, the Lua library registration), but they are filled at start-up by the executable and closed afterwards. Modding the original means one of:

- **Replacing files** inside the game's archives (SnakeBite installs packages).
- **Overriding Lua**: the game's scripts are plain Lua 5.1, so a mod can wrap or replace script functions (Infinite Heaven works this way).
- **Hooking native code** at fixed addresses (IHHook plugins), which only works for one build of the executable and breaks when it changes.

All three work, but conflicts are silent (two mods replacing the same file or function: the last one wins and nobody is told), and the only test is to play.

## How our engine does it
1. **Manifest check**: namespace (lower case, unique), API version (during 0.x the minor version must match exactly), kind (Python or Lua), dependencies.
2. **Load order**: vanilla first, then every mod after what it depends on (`depends`, `after`, `before`); when nothing decides, alphabetical by namespace. The order never depends on the folder listing or the run.
3. **Registration**: each mod's register step runs with a context bound to its namespace. Every change is journaled; if any mod in the set is refused, the whole set is undone and the error names the mod.
4. **Runtime**: engine code reads the registries. At three named engine calls, **hook sites**, mods may watch, change or stop the call:

| Site | Engine call | Cancelling means |
|---|---|---|
| `route.switch` | a soldier moves to the next leg or node event of its route | the soldier stays where it is |
| `cp.phase_change` | a base (command post) changes phase | the base keeps its phase |
| `command.dispatch` | a `SendCommand` reaches its handler | the handler is not called |

Before hooks run in load order, after hooks in reverse, so the first loaded mod wraps the outside. Hooks see read-only snapshots of the base, the soldier or the player, never the engine's live objects.

Lua mods run in a **sandbox**: no files, no operating system, no clock, no `require`, no precompiled code, and at most 10 million Lua instructions per call. Python mods are trusted and not sandboxed: they are for your own prototypes.

## Benefits
- **Conflicts are found, not hidden.** Two mods registering the same name, or two message names that hash to the same 32-bit id, are refused with both mods named. The project found real colliding names by brute force and uses them in the tests.
- **Predictable effects.** A change can be checked before anyone plays. Example from the tests: raising the alert drain rate from 1/30 to 1/20 per second shortens the recorded alert drain from 1,798 to 1,199 frames, exactly what arithmetic predicts, and the caution and evasion phases do not change at all.
- **Replayable.** Randomness comes only from the engine's seeded generator; the same mods and the same seed give byte-identical results. A double run catches a mod that reads the clock or unseeded random numbers.
- **Nothing changes by accident.** With an empty mod loaded, every earlier test passes byte for byte. With only vanilla loaded, the engine behaves exactly like the original.
- **Cheap.** Reading values through the registries costs at most about 3 % frame time against the old hardcoded path (measured: 0.5 to 1.8 % on the soldier scenarios, 0.9 to 3.2 % on the frame-loop scenario; the budget is 5 %).
- **Shareable safely.** A Lua mod cannot read your files or reach the network.

## Pitfalls and limitations
- **The engine is not a game yet.** It runs headless: no graphics, sound or input until M20 to M22. A mod today changes a simulation that tests compare with the real game, nothing you can play.
- **Private for now.** The engine's repository is private; the API exists to be published later.
- **API 0.x is not stable.** Until M24 freezes version 1.0, a mod written for 0.1 is refused by 0.2. Expect breaking changes.
- **Few hook sites.** Three so far. The caution / evasion route switch is not ported yet, so it is not a hook site.
- **Most handlers are names only.** All 514 vanilla command handlers are registered so their names are reserved, but none of them is implemented yet; chaining onto one fails until its milestone ports it.
- **Natives are mostly recorded.** The game's Lua still gets many answers replayed from a recorded session; a mod library cannot call real game systems that do not exist in the engine yet.
- **Cancelling is blunt.** A cancelled phase change keeps the old phase but does not touch the timer; a cancelled route switch keeps the soldier on its record until something else moves it.
- **Hooks have a cost the budget does not cover.** A site with no hooks is nearly free; a hooked site costs what the hooks do.
- **Python mods are not sandboxed.** Never load one you have not read.
- **One open question:** the order of a mod listener relative to the mission script's own update (E45).

## How we know
- `test_m10_registry.py`: every registry equals the table it came from; two builds give identical dumps.
- `test_m10_null_mod.py`: an empty mod changes nothing in the M3, M4 and M9 scenarios.
- `test_m10_ref_mods.py`: nine reference mods, one per extension kind, each against a fixture and an independent prediction.
- `test_m10_rejects.py`: every refusal with a real case, including genuine hash collisions.
- `test_m10_load_order.py`: two mods on one value or one hook site resolve the same way for every input order and every run.
- `test_m10_perf.py`: the 5 % frame-time budget.
- `test_natives_owned.py`: every native and every command handler has the milestone that must implement it.

---
<small>Hand-written article (`docs/site/explain/Mod-API.md`) &middot; published 2026-11-05.</small>
