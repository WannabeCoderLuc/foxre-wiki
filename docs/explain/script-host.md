# The Lua script host

*Milestone M4 (PASS, 2026-10-29). Reference: [Script host](../engine/script-host.md). Related: [How a mission loads](mission-load.md).*

## What it is
Most of what makes MGSV *MGSV* is written in Lua, not in the executable: the start-up sequence, the title screen, which packages a mission needs, where enemies patrol, when a cutscene plays. The executable provides building blocks (load a file, spawn a soldier, play a sound) as **native functions** that Lua calls. The *script host* is the part of an engine that runs that Lua and answers those calls.

## Why it matters
If a new engine runs the game's own Lua and answers its native calls the way the original does, a large part of the game's behaviour comes along without being rewritten. The script host is also where most mods live: Infinite Heaven, for example, is almost entirely Lua.

## How the original does it
- **Interpreter.** The game uses **stock Lua 5.1**. The only internal change is where a string keeps its characters (behind a pointer instead of inside the string object). Tables are stock too. Lua code never notices; native tools that read Lua values from memory must.
- **The API.** At start-up the game registers **5,532 native functions in 399 libraries** (`Fox`, `GameObject`, `TppUiCommand`, `Mission`, ...). It uses four mechanisms: stock `luaL_register`, a table builder whose constants are tiny functions, class tables (`TppSoundDaemon{}` creates an object), and direct field sets. 74 functions are empty in the release build, among them `print` and `Fox.Log`.
- **Boot.** The engine runs a few class scripts, `init.lua`, then `Tpp/start.lua` as a **coroutine resumed once per frame** (so loading can spread over frames), then starts the start-up mission. From cold boot to free roam the game loads **170 script chunks** in a fixed order, apart from a few that run on worker threads.
- **Messages and timers.** Scripts react to events: a timer ending, a popup closing, the online login finishing. The engine queues these as messages and hands them to the mission script's `OnMessage` once per frame.
- **The start-up screens.** The start-up mission walks through about 25 steps: language, save check, autosave notice, loading the save, the Konami server login (offline it shows two "connecting" notices and a "could not connect" notice, then carries on), the DLC check, and finally a screen inside the executable that calls the Lua function that picks and loads the title screen. Which title screen (Afghanistan, Africa, the hospital) is decided by the save.

## How the new engine does it
- `Engine/script/host.py` runs the game's own `init.lua` and `start.lua` in a Lua 5.1 interpreter and creates every library **at the same point of the boot** as the game, from the binding map captured live.
- **Implemented natives** come from decompiled code: file loading, `ScriptBlock.*`, the mission loader, `TppScriptVars` declarations and save slots, timers, popups, the offline login, the DLC check, the pre-title screen, the language change, bit operations and others.
- **Record and replay** covers the rest: a log-only plugin records what each native returned in a real session (now including whole tables); the host answers with those recordings. About 95 % of the API the host touches is answered this way or natively.
- **The save decides, as in the game.** The host loads a recorded save only through the same save-slot calls the game's scripts make, so the start-up mission picks the title screen and the free-roam mission from it.

## How we know it is right
- **Chunk order:** 112 of 112 boot chunks and 58 of 58 from there to free roam, in the live order (one UI package runs on a worker thread and is checked as a group).
- **Start-up screens:** the host walks the same 24 steps as a recorded game session, with the same messages in the same order.
- **Free roam with messages on:** for a save that continues in Africa, the host loads the same title screen and free-roam mission as the real game and reaches free play; the only script error left is a map lookup that belongs to the next milestone.
- **Call log:** the host's list of native calls is compared with a recording of the real game. 548 functions are called on both sides, 517 of them with the same arguments, in nearly the same first-call order (95 %). Every function called on one side only is explained (mostly Infinite Heaven, which was active in the recording, and the title menu, which waits for M6).

## Still open
- **The title menu** needs a map lookup by name (world data), so it moves to M6; until then the tests press "Continue" themselves.
- A short list of argument differences, mostly from save data and Infinite Heaven's quest choice in the recording.
- When a script adds keys to a table while looping over it, the real game does not visit the new keys but the host's Lua does; harmless today, tracked as E29.
- Class-instance calls for graphics and UI (`UiDaemon:`, `PhDaemon:` ...) are still answered by empty stubs.

---
<small>Hand-written article (`docs/site/explain/Script-Host.md`) &middot; published 2026-10-29.</small>
