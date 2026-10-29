# For modders: findings at a glance

*Plain-language summary of the project's findings that matter when you mod MGSV:TPP (build 1.0.15.4, Steam EN). Each point links to the reference page with the exact details. Tags as on the rest of the site: [V] verified in the game's code or live, [I] inferred, [?] open. Addresses are for 1.0.15.4 EN only.*

## The short version
- Every game file container we read can be **read and written back byte for byte**, so tools built on our readers cannot corrupt data by accident.
- The Lua side of the game is **ordinary Lua 5.1**: anything you can do in Lua you can test offline, before the game ever sees it.
- **Lua files inside a package run automatically** when that package loads. That is how missions, locations and script blocks get their code, and the cleanest way to add your own.
- **Which packages a mission loads is decided in Lua** (`TppMissionList` / `TppPackList`), not in the executable. You can add or swap packages without touching the exe.
- We have a **list of every native Lua function the game registers** (5,532 of them, with their addresses), plus recorded examples of what many of them return in a real session.

## Step-by-step guides
| Guide | Finding it builds on |
|---|---|
| [Add a package to a mission](add-a-package.md) | mission package lists are decided in Lua |
| [Run your own Lua from a package](lua-from-packages.md) | package scripts run on load, in path order |
| [Find and call Lua natives](lua-natives.md) | binding map of 5,532 natives, recorded return values |
| [Side content with script blocks](script-blocks.md) | 8 script-block slots with their own lifecycle |
| [Patching the iDroid tables](idroid-tables.md) | the iDroid reloads its tables on every language change |
| [Editing fox2 DataSets](editing-datasets.md) | the engine's type registry, byte-exact DataSet codec |
| [Tracing the game with FoxTrace](foxtrace.md) | log-only hooks and native return recording |
| [Ground height at any point](ground-height.md) | terrain block placement, tiling and the game's triangle rule |
| [Checking community addresses](claims.md) | 3,018 community facts checked against the executable |

## 1. Files and packages
**What we found.** The game stores files in `.dat` archives (QAR), which hold packages (`.fpk` for assets, `.fpkd` for data and scripts), which hold DataSets (`.fox2`), routes (`.frt`), navmeshes (`.nav2`) and scripts (`.lua`). Our readers and writers reproduce all 134,241 archive entries, 16,354 packages, 44,994 DataSets, 307 route files and 840 navmeshes exactly [V]. Details: [Game data](../explain/game-data.md), [QAR](../formats/qar.md), [FPK](../formats/fpk.md), [FOX2](../formats/fox2.md), [FRT](../formats/frt.md), [NAV2](../formats/nav2.md).

**How it works.** Names inside the game are hashes, not text. A file path becomes a 64-bit PathCode, other names a StrCode32/64 [V]. That is why you sometimes see numbers where you expect names: the name list we have covers 83 % of archive entries.

**Use it for.**

- Repacking: changes made with our codecs re-encode exactly like the original, so a diff of your package shows only your change.
- Finding things: a path hash in a package or in the exe is enough to find the file (our tools compute PathCode64 / StrCode for any string).
- Script files in packages are lightly obfuscated: a byte `0x1B` / `0x1C` header means "XOR with a key from the file name" (`0x1C` is also compressed). Our reader decodes both [V]; plain-text `.lua` files are accepted by the game as they are.

## 2. Classes, entities and DataSets
**What we found.** The engine knows 1,153 classes with 6,062 typed properties (exported from the game's own registry) [V]. A `.fox2` DataSet is a list of entities of those classes. See [Classes and entities](../explain/classes-and-entities.md) and [Reflection](../engine/reflection.md).

**Use it for.** Writing or editing `.fox2` files with the right property types and containers; knowing which properties a class really has before you add an entity. Several entity classes are "loaders" that make the engine do something when their DataSet loads; the useful ones are listed below.

## 3. The Lua environment
**What we found.** Details: [Script host](../engine/script-host.md).

- The game runs **stock Lua 5.1**. The only internal change: a string's characters sit behind a pointer instead of inside the string object [V]. That matters only to native hooks that read Lua strings from memory (IHHook, FoxTrace); Lua code never sees it.
- **5,532 native functions in 399 libraries** are registered, through four different mechanisms (stock `luaL_register`, a table builder, class tables, direct field sets) [V]. Our binding map gives every name with its address.
- **74 natives are empty in the release build**, among them `print`, `Fox.Log`, `Fox.Warning`, `Fox.Error` [V]. Logging through them does nothing; use your own file output (as Infinite Heaven does).
- Many constants are **closures, not numbers** in the builder libraries (reading them works as usual; they just are not plain table values) [V].
- The game replaces `pairs` / `ipairs` with versions that also walk engine property arrays [V]. Plain tables behave as usual.
- `Script.LoadLibrary(path)` is **synchronous and loads a file only once**; a returned table becomes the global named after the file, and its `requires` list loads right after it [V]. `Script.LoadLibraryAsync` finishes on a later frame.
- The boot runs `init.lua`, then `Tpp/start.lua` **as a coroutine resumed once per frame**, then `Tpp/Scripts/System/start2nd.lua`, and only then starts the init mission (`TppVarInit.StartInitMission()`) [V].
- `mvars` is created by the engine: it is set to a fresh empty table whenever a mission object is created or destroyed [V]. Do not keep anything in `mvars` across missions.
- `gvars` and `svars` are declared from Lua lists (`TppScriptVars.DeclareGVars` / `DeclareSVars`); arrays are 0-based [V].

**Use it for.**

- Knowing which native exists, what it is called and where it lives before you hook or call it.
- Not wasting time on `Fox.Log`.
- Testing Lua offline: our engine host (`Engine\script\`) boots the game's own `init.lua` and `start.lua` with no game running and reproduces the game's own script load order, from cold boot through the start-up mission to free roam (M5 PASS). A mod's Lua can be run in the same environment to catch errors early.

## 4. How a mission gets loaded
**What we found.** Details: [Resources and mission load](../engine/resources.md).

1. Lua (`TppMission.Load`) sets `vars.locationCode` / `vars.missionCode` and calls `Mission.LoadLocation()` and `Mission.LoadMission()`. These only **request** the load [V].
2. On later frames the engine asks two Lua functions which packages to load: `TppMissionList.GetLocationPackagePath(locationCode)` and `GetMissionPackagePath(missionCode)` (registered with `Mission.SetLocationPackagePathFunc` / `SetMissionPackagePathFunc`) [V]. They return a list of package paths.
3. The location loads first (its own package plus a "common" package named in the stage's `.fstb` file, e.g. `afgh_common.fpk`); the mission packages load only once the location is ready [V]. If only the mission changes (same location), the location stays loaded.
4. **Every `.lua` file inside a loaded package runs right away**, package by package in list order. Within one package they run in **reverse of the order they are stored**, which in every game package equals alphabetical path order [V]. A returned table becomes a global named after the file.
5. The mission's `TppSimpleMissionData` entity (in the mission package) names the main script (`mission_main.lua`) and the sub-scripts (`sequence`, `enemy`, `demo`, `radio`, `sound`, ...). The engine then runs `OnAllocate(subScripts)` and `OnInitialize(subScripts)` of the main script, each as a coroutine resumed once per frame; when `OnInitialize` returns, the mission becomes active [V].
6. Extra packages are added by the game itself: every mission except 30050 also gets two vehicle colouring packages (`mfv_scol_c11.fpk`, `mfv_scol_c07.fpk`) [V].

**Use it for.**

- **Adding a package to a mission**: add its path in `TppMissionList` / `TppPackList` (e.g. `TppPackList.AddMissionPack("/Assets/.../mypack.fpk")` inside the mission's pack-list function). No exe change needed.
- **Adding code to a mission**: put your `.lua` inside a package that the mission loads. It runs on load, and its returned table becomes a global you can call from the mission's scripts. Name the file so its alphabetical position gives the run order you need.
- **Adding a mission sub-script**: add a key to `TppSimpleMissionData.subScripts` that points at your script; it is then handed to `OnAllocate` / `OnInitialize` with the others.
- Understanding why a script "runs twice": `mission_main.lua` is in several packages and really does run once per load.

## 5. Script blocks (quests, reinforcements, animals)
**What we found.** Side content loads into **8 global script-block slots**. A slot exists while a `ScriptBlockData` entity of a loaded DataSet exists [V]. Lua drives them with `ScriptBlock.Load(id, packages)`, `Activate`, `Deactivate`, `Reload` and reads `GetScriptBlockState` (EMPTY 0, PROCESSING 1, INACTIVE 2, ACTIVE 3) [V]. The block's script gets `OnAllocate`, `OnInitialize`, then `OnUpdate` every frame and `OnTerminate` before unloading [V]. Quest and animal blocks are saved in `svars.sbl_*` and restored when you continue a save [V].

**Use it for.** Custom quests or side content that should load and unload with the area instead of living in the mission package: same package rules as above, driven through `TppScriptBlock` / `ScriptBlock.Load`.

## 6. The iDroid UI reloads on language change
**What we found.** The iDroid's map/pause tables (`mbdvc_*_parameter.lua`, `mbdvc_pause_help_table.lua`) live in the package `/Assets/tpp/pack/mbdvc/mb_dvc_top.fpk`. The UI loads it as the last step of every language change: each `TppUiCommand.ChangeLanguage()` sets a "change pending" flag (`TppUiCommand.IsChangeLanguage()` reads it), the iDroid reloads fonts, texts and then `mb_dvc_top`, and clears the flag [V]. A normal start-up calls it **three times**: `TppUiBootInit.lua` during the boot, `init_sequence` after reading the config save (`Seq_Demo_SetSavedLanguage`), and again while loading the save data (`CreateOrLoadSaveData`) [V live]. Even with the same language every call reloads. `emblem_list.lua` is loaded by the emblem setup (`0x1405CF950`) shortly after the start-up mission's package [V].

**Use it for.** If you patch those tables, expect them to run at least three times per start-up and again on every language change in the options; keep your changes in the package (or re-apply them after `IsChangeLanguage()` turns false) rather than patching the globals once. Calling `ChangeLanguage()` yourself is a way to force the iDroid tables to reload.

## 7. Watching the game: FoxTrace
**What we found / built.** FoxTrace is a log-only plugin (loaded by IHHook) that hooks functions without changing game state and writes one JSON line per event [V]. Version 3 adds `luaret` hooks that record **what a native Lua function returned**, per argument list, for any `lua_CFunction` or the two internal call thunks (`0x1400F6630` class functions, `0x141A154D0` builder functions) [V]. Our recordings cover 663 natives over identical repeated runs.

**Use it for.**

- Finding out what a native returns in a real session before you rely on it (many are undocumented).
- Seeing the exact order in which the game loads scripts and packages (hook `luaL_loadbuffer` at `0x141A178E0`).
- Two practical lessons from building it: enable all MinHook hooks in one call (enabling them one by one while the game boots misses early calls), and keep hook names short in config files.

## 8. Community addresses, checked
We imported 3,018 facts from IHHook, Infinite Heaven, V_Framework and the community wiki and checked them against the executable: 1,071 confirmed, 5 contradicted, the rest not checkable yet. See [Claims ledger](../engine/claims.md) and [Contradictions](../engine/claims-contradictions.md). In short: four IHHook address-table entries (three of them commented out in IHHook) and one wiki address point into the middle of other functions in 1.0.15.4 EN. Use commented-out IHHook entries as hints only.

## 9. Terrain: ground height without a game function
**What we found.** No script function returns the ground height, but the `.htre` block files do, exactly: block `<loc>_<bx>_<bz>` starts at ((bx − 133) × 128, (bz − 133) × 128), its heights are stored as 32 × 32 tiles, and the ground between samples is two triangles per 2 m square [V live, within 5 mm]. A player standing on flat ground has `vars.playerPosY` = ground + 0.798 m.

**Use it for.** Placing objects or warps on the ground offline, without probing in game. See [Ground height at any point](ground-height.md).

## 10. Limits
- Addresses are for **1.0.15.4 EN**; other builds differ.
- Our engine host runs scripts **without rendering, physics or AI**; it answers engine calls from recordings or simple models. It shows script behaviour and load order, not gameplay.
- Statements tagged [I] or [?] are not proven; check the reference page before building on them.

## Where to look next
- Reference pages: [Script host](../engine/script-host.md), [Resources and mission load](../engine/resources.md), [Engine modules](../engine/modules.md).
- Source code (private repository for now): `Engine\formats\` (readers/writers), `Engine\script\` (Lua host), `Engine\resources\` (package and block loading), `Tools\FoxTrace\` (tracer).

---
<small>Hand-written article (`docs/site/mods/For-Modders.md`) &middot; published 2026-10-29.</small>
