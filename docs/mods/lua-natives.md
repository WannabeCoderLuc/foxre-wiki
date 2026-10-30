# Find and call Lua natives

*Based on: [The Lua script host](../explain/script-host.md). Exact details: [Script host](../engine/script-host.md).*

## The finding
The game registers **5,532 native functions in 399 libraries**, through four mechanisms, at known points of the boot [V]. The project's binding map lists every name with its address and the boot point at which it appears. 74 natives are empty in the release build (shared empty function), among them `print`, `Fox.Log`, `Fox.Warning`, `Fox.Error` [V]. Recordings from real sessions show what 663 natives returned for the arguments they were called with [V live].

## How it works
- **Libraries appear during the boot.** A mod module that runs early may see a library missing; the binding map says after which script chunk it exists.
- **Builder constants are closures.** In the table-builder libraries, constants are tiny functions; reading them works as usual, but `type()` says `function` and `pairs` sees hashed keys.
- **Class tables are callable.** `TppSoundDaemon{}` creates an instance; methods are called as `inst:Method()`.
- **`pairs` / `ipairs` are replaced** by versions that also walk engine property arrays; plain tables behave as usual.

## How this would be used in a mod
*Hypothetical example.* A mod wants to know whether the language reload has finished before it re-applies its iDroid changes. The binding map lists `TppUiCommand.IsChangeLanguage` (decoded: it returns the language service's "change pending" flag), so the mod polls it from an update function instead of guessing a delay:

```lua
if not TppUiCommand.IsChangeLanguage() and not this.applied then
  this.ApplyIDroidPatch()
  this.applied = true
end
```
The same check works for any native: look it up in the binding map, read the Reference page for its decoded behaviour, and use a FoxTrace recording to see what it returns in a real session before relying on it.

## Pitfalls
- A native that exists may still be a no-op; check whether it is one of the 74 stripped functions.
- Addresses are for 1.0.15.4 EN only; names are stable, addresses are not.

---
<small>Hand-written article (`docs/site/mods/Lua-Natives.md`) &middot; published 2026-10-30.</small>
