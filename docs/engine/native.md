# Native backend

Clean-room engine design, no RE: a C++ copy of Python query code that already equals live (M7, M8). Module `Engine\native\`. Planned by [`docs\ROADMAP.md`](../status/roadmap.md) "Implementation language & native boundary" (Luc 2026-10-29) from M9; that step was never built because no M9 gate item required it. Built 2026-11-05 to close M10 common gate C7 (Luc kept C7 open, 2026-11-05).
Tags: [B] built and tested, [P] planned, [D] design decision.

## Boundary [D]
- **New engine code is C++ only (Luc, 2026-11-05).** Every new engine module or system is written here in C++ and verified by pytest through its pybind11 binding directly against the live fixtures and game files of its gate items; no Python version is written first.
- **Existing Python modules are the frozen reference.** A C++ copy of one (a port) must give **bit-identical** results on the same inputs (`cpp == py`, common gate C7); a port without a passing oracle is not used. Python modules get bug fixes only; one that needs new behaviour is ported first, then extended in C++. All are ported by M23 (G1). Ported so far: height sampling (M7), the nav path job (M8).
- **Stays Python:** `Tools\` (incl. the MOD-A toolkit), MCP servers, pytest verifiers and harnesses, fixture generators, build scripts, and the byte-exact format codecs (`Engine\formats\`) that tools and tests use; the runtime reads typed data through C++ query objects.
- **Same signatures (ports).** Query objects take contiguous buffers (`numpy` float32 / uint arrays, `bytes`); the Python class keeps parsing and owns the data, the native object is built from it once and answers queries.

## Writing a new C++ module [D]
1. Spec first (`docs\engine\` / `docs\formats\`, skills `fox-system` / `fox-format`); gate items and test names in the ROADMAP list, then `Tools\gates_sync.py`.
2. Sources `Engine\native\src\<module>.cpp` (+ `.h`) with one `bind_<module>(py::module_&)` called from `module.cpp`; `build_native.py` compiles every `src\*.cpp`.
3. Data in through contiguous buffers (`numpy` arrays, `bytes`) from the Python codecs; C++ parses files only where the runtime streams them (M23).
4. Tests `Engine\tests\test_<milestone>_*.py` import the binding (fail, never skip, when it is missing or stale: `Engine.native.backend("cpp")`) and compare against live fixtures / game files; the C4 double run goes through the binding.
5. float32 where the exe uses `float` (the spec says which), else `double`; `/fp:strict`; no wall clock, no unseeded randomness.

## Module and build [B C7]
- `Engine\native\src\`: `heightfield.cpp`, `navigation.cpp`, `module.cpp` (pybind11 module `_foxnative`). `Engine\native\__init__.py`: backend selection (below), `available()`, `SOURCE_SHA`.
- Build: `python Tools\build_native.py` (setuptools + `pybind11.setup_helpers.Pybind11Extension`; MSVC 2022 14.44, Python 3.13, pybind11 from pip). Output `Engine\native\_foxnative.cp313-win_amd64.pyd` (never committed: `.gitignore`). The module embeds the sha256 of its sources; `build_native.py` does nothing when the built module matches the sources.
- Compiler flags: `/O2 /fp:strict /std:c++17`. `/fp:strict` forbids contraction into FMA and reassociation; x64 code uses SSE2 scalar `float` / `double`, so every operation rounds exactly like numpy float32 and Python float64.

## Backend selection [D, Luc 2026-11-05]
- `ENGINE_BACKEND` = `auto` (default): C++ when `_foxnative` imports and its `SOURCE_SHA` equals the current sources, otherwise Python. A stale or missing module is never used by `auto`.
- `ENGINE_BACKEND=py`: Python only. `ENGINE_BACKEND=cpp`: C++ required; a missing or stale module raises at construction.
- Per object: `HeightField(..., backend=None | "py" | "cpp")`, `NavWorld(backend=...)`; `None` follows `ENGINE_BACKEND`. `obj.backend` says which one answers.
- Each native function is listed below with its state; `auto` only uses functions marked [B].
- The M7 / M8 gate tests pass on both backends (`ENGINE_BACKEND=auto` and `=py`, 2026-11-05).

## Equivalence rules [D]
- **Floats:** Python `float` (float64) arithmetic -> C++ `double`; each `f32()` / `np.float32(...)` rounding -> a `(float)` cast at the same point; numpy float32 expressions -> C++ `float` with the same operation order. No `-ffast-math`, no FMA.
- **Integers:** Python floor division and `math.floor` -> `std::floor` on the same double; `int(x)` truncation -> cast toward zero; unbounded Python ints only where values fit in 64 bits (checked by the oracle).
- **Order:** Python dict insertion order -> insertion-ordered vectors; `sorted` / `min` / `max` ties -> the first in Python's order; `heapq` -> a binary heap on the same tuple key with the same tie-breaker. Where Python iterates a `set` and the order can reach a result, both sides switch to an ordered equivalent first (Python output unchanged, checked by the M8 gate).
- **Oracle:** `Engine\tests\test_cpp_equiv.py` runs both backends on the same objects and compares bit patterns (float32 / float64 bits, status strings), not tolerances.

## Native functions
| Function | Python original | C++ | State |
|---|---|---|---|
| `HeightField.sample(x, z)` | `Engine\world\heightfield.py` | `heightfield.cpp` `sample` | [B C7] |
| `HeightField.sample_many(xz)` | new, = `sample` per row | `heightfield.cpp` `sample_many` | [B C7] |
| `NavWorld.find_path(...)` (all six stages: locate / seed, A*, cluster, region, corridor, relax, ray, extender; runtime meshes and dynamic links), `locate`, `in_loaded`; the triangle grid is built in C++ | `Engine\world\navigation.py` | `navigation.cpp` `NavCore` | [B C7] |
| CPython float helpers: `math.hypot` / `math.dist` (`vector_norm`), float `//`, `x ** 2` | CPython 3.13 | `pyfloat.h` | [B C7] (200,000 seeded inputs) |

## Data flow (nav) [D]
`NavWorld.add_file` parses as before and forwards each mesh (`_Mesh` arrays and raw bodies `b0`, `b1`, `b3` with their offsets, key, block, origin, scale) and each tile tail to `NavCore`; the triangle grid is rebuilt in C++ in the same order. `set_loaded`, `set_blocked`, `set_runtime` forward their state (runtime meshes built once per state, as in Python). `find_path` returns the path and sets `status` from the native answer.

## Measured [B C7, 2026-11-05]
Printed by `test_cpp_equiv.py` (one run, reference PC; not gated, speed gates are M14 G7, M17 G6, M22 G4, M23):

- **Nav path job:** 948 `m8_nav_jobs` (614 ok, 25 coarse, 309 unloaded) 1.51 s Python -> 0.078 s C++ (about 19x); all bit-identical, and all 410 `m8_nav_paths` requests.
- **Heights:** 100,000 samples 0.62 s Python; C++ one call per sample 0.18 s (call overhead dominates), `sample_many` 0.002 s (about 300x); 200,036 points bit-identical on the .htre mosaic and the .tre2 field.
- Load time: `NavWorld.add_file` still parses in Python; the triangle grid is built in C++ (the Python grid is skipped under the C++ backend).

## Extension points
- **Native plugins** (M24): mods may ship a native module only through the same rule: a Python reference plus a `cpp == py` oracle in the mod's own tests; the loader never loads a native module from a Lua mod (sandbox, `ModAPI.md`).
- New hot paths join the table above with their oracle; the common gate C7 then covers them for the milestone that owns them.

## Evidence
- `Engine\tests\test_cpp_equiv.py` (M10 C7): every `m7_ground_heights.json` point and 100,000 seeded points over the same blocks and the `.tre2` field; every job of `m8_nav_jobs.json` (948) and every request of `m8_nav_paths.json`; bit-identical results and equal `status`; backend selection (`auto`, `py`, `cpp`, stale module).
- The Python originals equal live: `test_m7_ground.py` (heights within 5 mm), `test_m8_nav.py` (948 of 948 jobs within 0.1 m). The M7 / M8 gate tests run on the default backend and with `ENGINE_BACKEND=py`.

## Open
- The ray's side tests compare float32 inputs in double precision (`Navigation.md` "Engine module", [I]); the C++ copy keeps the Python rule, so `cpp == py` holds; whether the exe uses float there stays open.
- Collision / raycast (M14) and the C++ frame loop (M23) are not started.

---
<small>Source: `docs/engine/Native.md` in the project repository &middot; generated 2026-11-06.</small>
