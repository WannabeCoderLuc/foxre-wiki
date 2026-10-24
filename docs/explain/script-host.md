# The Lua script host

*Milestone M4 (IN PROGRESS). Reference: [Script host](../engine/script-host.md). Related: [How a mission loads](mission-load.md).*

## What it is
Most of what makes MGSV *MGSV* is written in Lua, not in the executable: the start-up sequence, the title screen, which packages a mission needs, where enemies patrol, when a cutscene plays. The executable provides building blocks (load a file, spawn a soldier, play a sound) as **native functions** that Lua calls. The *script host* is the part of an engine that runs that Lua and answers those calls.

## Why it matters
If a new engine runs the game's own Lua and answers its native calls the way the original does, a large part of the game's behaviour comes along without being rewritten. The script host is also where most mods live: Infinite Heaven, for example, is almost entirely Lua.

## How the original does it
- **Interpreter.** The game uses **stock Lua 5.1**. The only internal change is where a string keeps its characters (behind a pointer instead of inside the string object). Lua code never notices; native tools that read Lua strings from memory must.
- **The API.** At start-up the game registers **5,532 native functions in 399 libraries** (`Fox`, `GameObject`, `TppUiCommand`, `Mission`, ...). It uses four mechanisms: stock `luaL_register`, a table builder whose constants are tiny functions, class tables (`TppSoundDaemon{}` creates an object), and direct field sets. 74 functions are empty in the release build, among them `print` and `Fox.Log`.
- **Boot.** The engine runs a few class scripts, `init.lua`, then `Tpp/start.lua` as a **coroutine resumed once per frame** (so loading can spread over frames), then starts the start-up mission. From cold boot to free roam the game loads **170 script chunks** in a fixed order, apart from a few that run on worker threads.
- **Loading files.** `Script.LoadLibrary(path)` runs a file now and only once; a table it returns becomes the global named after the file. `LoadLibraryAsync` completes on a later frame.

## How the new engine does it
- `Engine/script/host.py` runs the game's own `init.lua` and `start.lua` in a Lua 5.1 interpreter and creates every library **at the same point of the boot** as the game, from the binding map captured live.
- **Implemented natives** come from decompiled code: file loading, `ScriptBlock.*`, the mission loader, `TppScriptVars` declarations, the language change, bit operations and others.
- **Record and replay** covers the rest: a log-only plugin records what each native returned in a real session; the host answers with those recordings. Today the host answers about 93 % of the API it touches this way or natively.

## How we know it is right
The host must load the same chunks in the same order as the live capture. It does: **112 of 112** boot chunks before the start-up mission, and **58 of 58** from there to free roam (with the M5 mission loader). The one place where the order is not fixed is a UI package that runs on a worker thread during the boot; it lands in a different spot in every real run, so the test checks it as a group.

## Still open
- **Timers and messages to scripts.** The start-up mission's title flow begins when a timer sends a `Timer.Finish` message to the mission's `OnMessage`. The host has neither yet, so the tests make that flow's native requests themselves.
- **Instance methods** (`UiDaemon:`, `PhDaemon:` ...) and tables returned by natives are still answered by stubs or recorded as "a table" only.
- The M4 gate compares the full native **call log** against a live session; that comparison is not done yet.

---
<small>Hand-written article (`docs/site/explain/Script-Host.md`) &middot; published 2026-10-24.</small>
