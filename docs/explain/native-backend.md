# The C++ backend

*Built under M10 (common gate item C7; M10 PASS on 2026-11-05). Exact details: [Native backend](../engine/native.md). Related: [How soldiers find their way](path-finding.md), [Terrain and collision files](terrain-and-collision.md), [How we verify](verification.md).*

## What it is
The new engine was first written in Python: easy to read, easy to test, and quick to change while the game's behaviour was still being worked out. The **C++ backend** is a second copy of the engine's busiest code, written in C++ and loaded into the same process, that gives exactly the same answers much faster.

Two pieces have a C++ copy today:

| Piece | What it answers | Python original |
|---|---|---|
| Ground height | the height of the ground at any point, from the game's height maps | M7 |
| Path job | the whole path a soldier asks for: locating the start and goal, the search, smoothing, obstacles and links | M8 |

Since 2026-11-05 every new engine system is written in C++ directly (Luc's rule). The Python modules that already exist stay as a frozen **reference**: they get bug fixes, and a module that needs new behaviour is first copied to C++, checked, and then extended there.

## Why it matters
- **Speed.** The engine will run thousands of path jobs and ground queries per second once a whole area runs (M17) and later a playable game (M22). Measured on the project's PC: the 948 recorded path jobs take 1.51 s in Python and 0.078 s in C++ (about 19 times faster); 100,000 ground heights asked in one batch take 0.002 s instead of 0.62 s (about 300 times faster).
- **One language for the final engine.** The standalone runtime (M23) is a native program. Code that is already C++ does not have to be rewritten later.
- **Nothing is lost.** The C++ copy is only used because it is proven to give the same bits as the Python version, which is itself proven against the real game.

## How the original does it
The original engine is C++ compiled into `mgsvtpp.exe`. Where the game computes in 32-bit floats, rounding happens after every single operation, and the order of operations decides the last bit. That is why the project measures its ground heights and paths against the game itself: the M7 ground heights match live within 5 mm, and the M8 paths match 948 of 948 recorded jobs within 10 cm.

The C++ backend contains no code from the game. It is a line-by-line copy of the project's own Python, not of the executable.

## How our engine does it
1. **Same steps, same rounding.** Every Python double-precision operation becomes a C++ `double`; every place where Python rounds to a 32-bit float becomes a cast to `float` at exactly the same point. The compiler is told not to merge or reorder floating-point operations (`/fp:strict`), so each step rounds the way Python and numpy do. Even a few helpers inside Python itself (how it computes a vector length, floor division and squares) are reproduced.
2. **Same order.** Where Python's result depends on the order things are visited (dictionaries, sorting ties, the search queue), the C++ copy visits them in the same order.
3. **Built from the sources, never stale.** `python Tools/build_native.py` compiles the module; the module carries a fingerprint of its sources, and the engine refuses a module that does not match the current sources.
4. **Default backend.** When the module is built and current, the engine uses C++ automatically. Setting `ENGINE_BACKEND=py` forces the Python reference (for comparisons), `ENGINE_BACKEND=cpp` makes C++ mandatory. A test or object can also pick its backend directly.
5. **Python still parses the files.** The format readers stay Python; they hand the C++ side plain arrays once, and the C++ side answers the queries.

## How we know
- **A bit-identical oracle**, `test_cpp_equiv.py`: both backends answer the same questions and their answers are compared bit for bit, not within a tolerance. Covered: all 948 recorded path jobs and all 410 recorded path requests; every recorded ground point plus 100,000 seeded random points over the same blocks and the coarse height field (200,036 heights); 200,000 inputs for the float helpers; and the backend selection itself (a stale module is never used).
- **The real game behind the Python version.** The M7 and M8 gate tests pass on both backends, so the C++ copy inherits their live evidence.
- **Common gate C7.** From M10 on, every milestone that touches code with a C++ copy must keep this oracle passing. The test builds the module first and fails, never skips, if there is no compiler.

## Limits
- Only two pieces are in C++ so far. The frame loop, scripts and soldier logic are still the Python reference; all of it is ported by M23.
- Speed is measured, not gated yet: speed gates come with M14, M17, M22 and M23.
- One open detail: a ray test in path smoothing compares 32-bit inputs in double precision. The C++ copy keeps the Python rule, so the two agree; whether the game does the same is not settled.
- Mods cannot ship native code yet. From M24, a mod's native plugin will have to follow the same rule: a reference version plus its own bit-identical test.

---
<small>Hand-written article (`docs/site/explain/Native-Backend.md`) &middot; published 2026-11-06.</small>
