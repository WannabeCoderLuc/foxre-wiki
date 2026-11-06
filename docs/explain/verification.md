# How we verify

*Why the specifications on this site can be trusted, and how to tell how sure each statement is.*

## Pass or fail, decided by a computer
Plausible-looking reverse engineering can still be wrong. So every milestone has a **gate**: an automated test that either passes or fails, written before the work counts as done. The tests run with `engine_verify` (pytest, `Engine/tests/`): a quick suite of 150 tests (2026-11-04) plus slow verifiers that read and write every game file mentioned on this site, and checks against every live fixture.

Since 2026-11-04 each gate is a list of numbered items (for example "raycasts: at least 5,000 of the game's own queries, hit point within 1 cm"), and every milestone from M10 on also has to pass a common gate: the whole test suite, specifications that say how mods can extend each system, the game's native functions really implemented instead of replayed, runs that repeat exactly, fixtures from at least two agreeing live runs, reference mods for every extension point, and a clean site build. A machine-readable list (`Engine/tests/gates.json`) names the tests that decide each item, and `engine_verify(gate="M10")` reports each item as passed, failed or not built yet.

## Three kinds of evidence
| Kind | How it works | Example |
|---|---|---|
| **Round trip** | read every file of a type and write it back; the bytes must be identical | 44,994 DataSets, 16,354 packages |
| **Emulator oracle** | run one function of the original game in an emulator and compare with our version | the game's string hash, including long strings |
| **Live fixture** | ask the running game, record its answers, and compare with our tools | 17 object names and positions in free roam |

Test files are locked with checksums, so a test can't quietly be changed to make broken code pass.

## Watching the game: FoxTrace and record/replay
Some facts can only be seen while the game runs. **FoxTrace** is a small log-only plugin (loaded by IHHook) that hooks chosen functions of the executable and writes one JSON line per call: arguments, the frame, the thread. It never changes game state. A capture boots the game twice with the same hooks; only results that agree across runs become test fixtures.

Version 3 adds **return recording** for Lua natives: it notes what each native returned for each argument list. The engine's script host can then answer those natives with the real game's answers (*record and replay*) while the natives are not implemented yet. Every capture is archived with its configuration, so a fixture can always be traced back to the run that produced it.

## Community knowledge, checked
Other projects (IHHook, Infinite Heaven, V_Framework, the modding wiki) already know many addresses and names. They enter as **claims**: a fact with its source, which counts only after one of our own checks confirms it (the function starts there, its byte pattern matches, the binding map has that name at that address ...). Of 3,084 claims, 1,109 are verified and 5 contradicted (counts as of 2026-11-04); see [Claims ledger](../engine/claims.md).

## Confidence tags
Statements in the reference pages carry a tag:

| Tag | Meaning |
|---|---|
| **[V]** verified | seen in the program's code or confirmed in the running game |
| **[D]** data | holds for every relevant file in the game data |
| **[I]** inferred | the most likely explanation, not yet proven |
| **[?]** unknown | open question |
| **[x]** corrected | an earlier claim that turned out wrong |

## Live runs near soldiers (M9)
Soldier behaviour varies between runs, so M9 added a **capture protocol**: the player cannot die (life refilled every second), clock and weather are fixed, the driver never touches the game by hand, warps go only to proven points, and no save is ever written during a run. A run with an unplanned event is marked and kept out of fixtures. A behaviour counts as pinned only when **two clean runs agree**; values that differ between runs (for example how long an alert lasts with a known target) are pinned as an order or a range, never as one number. Clamped runs (forced phases) and free runs are never mixed in one fixture.

## Names from a development build
Some function names come from a symbol map of a development build of the same executable. Such a name is [I] until the retail function body has been read and matches; only then is it used as a name on this site.

## Boundaries
- The game executable is never modified; all live checks use the game's own Lua interface or small logging plugins in single-player, offline.
- Code protected by Denuvo is not analysed; when a trace reaches it, the investigation stops there.
- No game files, extracted data or decompiled code are published.

## For modders
The same method protects a mod: keep a byte-exact round trip for every file your tool writes, check every address against a second source ([Checking community addresses](../mods/claims.md)), and repeat any live observation once before you rely on it. FoxTrace shows how to watch the game without changing it ([Tracing the game with FoxTrace](../mods/foxtrace.md)).

---
<small>Hand-written article (`docs/site/explain/Verification.md`) &middot; published 2026-11-06.</small>
