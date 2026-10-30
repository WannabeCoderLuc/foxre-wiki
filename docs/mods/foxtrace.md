# Tracing the game with FoxTrace

*Based on: [How we verify](../explain/verification.md). Exact details: [Script host](../engine/script-host.md) (record/replay), [Session log](../status/log.md).*

## The finding
FoxTrace is a log-only IHHook plugin: MinHook detours on chosen functions that record arguments, frame and thread to a JSON-lines file and change nothing [V]. Version 3 records **return values of Lua natives** (`luaret` hooks), per argument list, for any `lua_CFunction` and for the two internal thunks that call class and builder functions [V]. Hooking `luaL_loadbuffer` (0x141A178E0 in 1.0.15.4 EN) shows every Lua chunk the game loads, in order [V].

## How it works
A config file lists hooks, one per line:
```
hook loadbuf 0x141A178E0 L,i,i,s
hook mbdvc_top_load 0x14092B310 i,i
luaret TppUiCommand.ChangeLanguage 0x1408CE490 d per=64
maxlines 200000
```
Argument letters choose how each argument is logged (integer, float, string, Lua state ...). Captures are run twice; only results that agree become fixtures.

## How this would be used in a mod
*Hypothetical example.* A mod author's patched table seems to vanish at some point during start-up. They hook `luaL_loadbuffer` and `TppUiCommand.ChangeLanguage` and look at the log: the table file is loaded three times, each right after a `ChangeLanguage` call. That is the [iDroid reload](idroid-tables.md), and the fix is to re-apply after it. The same approach answers "when does my script actually run?" and "what does this undocumented native return?" without guessing.

## Practical lessons
- Enable all hooks in one MinHook call; enabling them one by one while the game boots misses early calls.
- Keep hook names short; log lines add up.
- Log-only means log-only: a hook that writes game memory is no longer a measurement.
- FoxTrace is part of the project's private tooling for now; the technique works with any IHHook plugin.

---
<small>Hand-written article (`docs/site/mods/FoxTrace.md`) &middot; published 2026-10-30.</small>
