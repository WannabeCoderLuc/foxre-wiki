# Mod API

Clean-room engine design for M10 ([`docs\ROADMAP.md`](../status/roadmap.md) M10, standing rules "Data-driven registries", "Determinism", "Compat mode").
Module `Engine\mods\`. API version **0.1** (0.x until M24 freezes 1.0). No new RE: this sits on M2-M9.
Tags: [B] built and tested (gate item named), [P] planned (gate item named), [D] design decision.

## Principles [D]
- **Vanilla is a mod.** Everything the engine knows about the original game is registered by the `vanilla` mod (`Engine\mods\vanilla\`) through the same `ModContext` calls a mod uses. Its manifest is fixed: namespace `vanilla`, load position 0, no dependencies.
- **Registries own the tables.** Engine modules read GameObject types, command handlers, message ids, updaters, AI tables, resource loaders, reflection classes, Lua libraries, natives and parameters from a `Registries` instance, not from module-level dicts. Module constants that carry measured values (`cp_phase.RATE`, `route_follow.STEP_NAMES` ...) stay as the vanilla mod's *source*; the registry is what consumers and mods see.
- **One `Registries` per engine instance**, never global: two hosts in one process (tests, double runs for C4) share nothing.
- **Compat mode:** with only `vanilla` loaded every M0-M9 gate passes unchanged (G1); with the null mod loaded traces are byte-identical (G2).
- **Determinism:** registration order is a pure function of the resolved load order; registries iterate in registration order; dumps are canonical JSON. No registry call reads time, randomness or the filesystem order.

## Registries [B G1]
`Engine\mods\registry.py`. Each kind is a `Registry` with entries `Entry(key, value, owner, impl, layers)`:

- `key`: the canonical key of the kind (below); `value`: JSON-able descriptor (what the dump shows); `impl`: optional Python callable / factory (not dumped); `owner`: namespace of the mod that registered it; `layers`: `(owner, value)` history of overrides, in load order.
- `register(key, value, impl=None)` adds a key; a key already present raises `Conflict` naming both owners.
- `override(key, value=..., impl=...)` replaces an existing entry's value and / or impl and appends a layer; the last loaded mod wins (order: section "Load order").
- Iteration (`items()`, `keys()`) is registration order. `dump()` = `{key: value}` in that order; `Registries.dump_json()` = canonical JSON of every kind (sorted keys inside values, kinds in fixed order).

| Kind | Key | Value (dumped) | Consumer today | Vanilla source |
|---|---|---|---|---|
| `gameobject_types` | type index (int, 0-127) | `{name, group}` | `GameObjectManager.register_from` (types with a manager factory) | `vanilla/gameobject_types.json` (type index table 0x142A7BA90, update groups of `m3_frame_trace.json`) |
| `commands` | `"<handler>:<Command>"` (vanilla: handler function VA; engine / mod types: the type index) | `{handler, owner, name, hash32, owner_milestone}` | `TypeManager.command` default dispatch (`handlers`) | `vanilla/commands.json` (knowledge DB `cmd_handlers.tsv`) |
| `messages` | StrCode32 id (int) | `{name, category, module}` | collision check for mod ids; bus routes by id | constants of `Engine\runtime\*`, M3 frame-trace messages |
| `updaters` | updater name (str) | `{priority, vtable, update}` | `UpdateService.register_from` (updaters with a factory) | `vanilla/updaters.json` (M3 live updater vector) |
| `ai_tables` | table name (str) | table as JSON | `route_follow`, `cp_phase`, `realize` (vanilla source today) | module constants of `Engine\world\` |
| `parameters` | dotted name (str) | `{value, type, bits?}` | `Registries.param(name)`; override target of G3 / G5 | `cp_phase` rates, realize budget / margins |
| `resource_loaders` | file extension (str) | `{type_id, codec}` | `Registries.codec_for(path)` | `pathcode.EXTENSIONS` + `Engine\formats\` / `Engine\resources\` codecs |
| `reflection_classes` | class name (str) | `{super, version, hash}` | `TypeDB` (vanilla source) | `fox_edb.json` via `Engine\core\typedb.py` |
| `lua_libraries` | library name (str) | `{kind, after_chunks, members, values}` | `ScriptHost.register_upto` | `m4_lua_bindings.json` |
| `natives` | `"Lib.Func"` | `{source, owner_milestone}` | `ScriptHost.natives` (a live view of this registry) | `ScriptHost` sources (loader, timers, popups, title, stage blocks ...) + recorded answers |
| `hooks` [B G3] | site name (str) | ordered list `[{owner, before, after}]` (bools); `impl` = the matching `[(owner, before_fn, after_fn)]` | `Engine\mods\hooks.py` `run_site` at the three sites | the three site names with empty lists (vanilla declares the sites; a mod's `ctx.hook` is an override layer) |
| `listeners` [B G3] | `"<ns>.listen<n>"` (n = 0, 1, ... per mod) | `{message, name}` (StrCode32 id, name if known) | `MessageBus.register_from` | none (vanilla's own listeners are engine objects) |

Not every vanilla entry has an implementation: GameObject types, command handlers and updaters are registered as **descriptors** (name, id, priority) so ids are reserved and collisions are caught, and get an `impl` when the owning milestone ports them (`commands_owner.json`, `natives_owner.json`, G7).

Kinds are dumped in the fixed order of `registry.KINDS` (12 kinds since G3; `hooks` and `listeners` last, so the first ten keep their G1 / G2 order).

## Registry consumers [B G1]
`Engine\mods\params.py`. Engine modules read measured constants through the registry, never from their module constants (those stay the vanilla mod's *source*):

- `params.param(name, reg=None)`: a parameter; `float32` parameters come back as `np.float32` rebuilt from `bits` (bit-identical to the constant), or from `value` when an override gives a plain float. `params.table(name, reg=None)`: an AI table.
- Every consumer function takes `reg=None`: the engine instance's `Registries`; without one it reads the **compat default**, a vanilla-only `Registries` built once per process and never loaded with mods (`params.default_registries()`). Mods always load into their own instance, so the default is vanilla by construction.
- Consumers today: `cp_phase.rate(phase, reg)` (`cp.rate.caution|evasion|alert`), `cp_phase.alert_end_max_timer(reg)` (`cp.alert_end_max_timer`), `cp_phase.investigators(reg)` (`cp.investigators`); `realize.select(..., reg)` (`realize.enter_margin`, `realize.stay_margin`, ai table `realize.zero_priority_bits`), `realize.unreal_move_speed(..., reg)` (`realize.unreal_crouch_scale`); `route_follow.already_at(..., reg)` (`route.same_spot_d2`), `route_follow.arrived(..., reg)` (`route.target_gate`, `route.arrive`), `route_follow.step_after(..., reg)` (`route.no_stop_events`, passes `reg` to `already_at`), `route_follow.step_name(step, reg)` (`route.steps`).
- With only vanilla (and with the null mod) every M9 gate test is unchanged and passes; an override in one instance changes only that instance (`test_m10_consumers.py`: alert rate x2 -> 901 frames to zero instead of 1800, float32). This is what G3's phase-rate override and MOD-B G1 build on.

## Ownership [B G7]
Standing rule ([`docs\ROADMAP.md`](../status/roadmap.md)): every native binding and every vanilla SendCommand handler entry has one **owning milestone**, which implements it, switches its recording off and keeps a call-log test (C3); M17 runs with zero recorded natives. Files (generated by `python Tools\m10_owners.py` from the tables below; `--check` in `test_natives_owned.py`):

- `Engine\tests\fixtures\natives_owner.json`: every member of every library in `m4_lua_bindings.json` (5,532 bindings, key `"<library>.<member>"` as the host names natives) -> `{owner, rule, status, implemented}`.
- `Engine\tests\fixtures\commands_owner.json`: every entry of the `commands` registry (514, `vanilla/commands.json`, key `"<handler>:<Command>"`) -> `{owner, rule, implemented}`.
- The vanilla mod copies the owner into the registry: `natives` and `commands` entries carry `owner_milestone` in their value.

**Status** (how a `ScriptHost(replay=m4_lua_returns)` answers the binding today, computed, never typed in): `native` (a registry native whose source is engine code), `static` (a value read statically from the exe: `values` of the bindings fixture or `m4_lua_consts.json`), `stripped` (the release build's shared empty function 0x141C658E0, 74 bindings; the host answers them with a no-op, exact because every recorded call of one returns nothing), `lua` (stock Lua 5.1 runtime), `foxmath` (`Engine\script\foxmath.lua`), `vars` (host variable tables: `vars`, `cvars`, declared gvars / svars) are **implemented**; `recorded` (answered from `m4_lua_returns.json`), `proxy` (`GetInstance` / constructor stand-ins) and `stub` (counted, returns nothing) are not.
**Owner rule:** an implemented binding is owned by the passed milestone that built it (table "Implemented by"); every other binding by the first library rule whose pattern matches the library name in full, and its owner must be a milestone that has not passed (M10 or later). A library no rule matches fails the test (no catch-all). Commands: the first command-name rule, else the handler rule.

| Rule | Implemented by | Owner | Why |
|---|---|---|---|
| I1 | `native:script.host`, `native:runtime.timers`, `native:runtime.popups`, `native:runtime.online`, `native:m4_lua_consts` | M4 | Script host and its gate-a runtime modules (`ScriptHost.md`). |
| I2 | `native:resources.*` | M5 | Resources and mission load (`Resources.md`). |
| I3 | `native:runtime.title`, `native:world.*` | M6 | Title menu, stage blocks, identifiers (`World.md`, `ScriptHost.md` "Title menu"). |
| I4 | `static:*`, `stripped:*`, `lua:*`, `foxmath:*`, `vars:*` | M4 | Built by the M4 host from the static binding map. |

| Rule | Libraries | Owner | Why |
|---|---|---|---|
| N1 | `_G\|coroutine\|package\|table\|io\|os\|string\|math\|debug\|bit\|metatable _LOADLIB\|metatable FILE\*\|io env \(.*\)` | M17 | Lua runtime: anything not stock is needed by the slice. |
| N2 | `foxmath\|Vector3\|Vector4\|Quat\|Matrix3\|Matrix4\|WideVector3\|Color\|metatable fox\..*` | M14 | Spatial math in strict float32 with the physics queries. |
| N3 | `vars\|cvars\|declared vars.*\|TppScriptVars` | M19 | Script vars and save slots (M19 G1 saves). |
| N4 | `Pad\|Pad2\|PadMapping\|PadType\|PlayerPad\|HidDriver` | M22 | Input bindings (M22 G3). |
| N5 | `Gr.*\|FxSystemConfig\|FxDaemon\|MaterialInfo.*\|ColorInfo\|TppEffect.*\|TppEyelidFilterStateManager\|TppCigaretteSmokeGlobalManager\|TppGenerativeClouds\|TppSky\|TppIsolatedSkidmarkFootprints\|TppRainFilterInterruptManager\|TppFadeOutEffectHolder\|TppColorCorrection\|TppOutOfMissionRangeEffect\|TppTonemap\|TppVolumetricFogManager\|TppLightProbe.*\|TppAtmosphere\|TppWeatherEffectManager\|AvatarPreloadTextureDaemon\|TppModelViewer\|TppHeliPhotoFova\|TppDataUtility\|HighSpeedCamera\|CameraPriority\|CameraSelector\|PlayerCamera` | M20 | Drawing, effects, cameras (M20 G2 / G4). |
| N6 | `LangDaemon\|LanguageBlock\|TppSoldierFace\|TppColoringSystem\|EnemyFova\|TppAnimalFova\|PlayerCamoType\|PlayerPartsType` | M11 | Language, fova and coloring files (M11 G7 / G8). |
| N7 | `SoundCoreDaemon\|SoundDaemon\|TppSoundDaemon\|TppMusicManager\|TppMusicPlayer\|Sound(Player\|Soldier\|Animal)AnimEvent\|VoiceCommand\|Subtitles(Daemon\|Command)\|RadioDaemon\|TppRadioCommand\|LipSyncDaemon` | M12 | Sound events, music, voice, radio (M12 G1 / G2). |
| N8 | `Ui.*\|TppUi.*\|HudCommonDataManager\|Popup\|GamePauseMenu\|MbPauseHelp\|GameOverMenu\|CountrySettingMenu\|SplashScreen\|TppPause\|TppPauseMenu\|PauseController\|TppMarker2System\|FadeFunction\|FoxFadeIo\|TppVideoPlayer\|DemoxUi\|TppEula\|TppEnding\|ActionIcon\|CallMenuEventCategoryType\|AvatarEdit\|TppCassetteTapeInfo` | M12 | Menus, HUD, markers, fades, popups (M12 G4 / G5). |
| N9 | `StageBlock\|StageBlockCurrentPositionSetter\|ScriptBlock\|PassiveBlockController\|BlockGroup\|ObjectBrushBlock\|TppCyprusBlockControl\|LuxuryBlockController\|Time\|FoxGameFrame\|WeatherManager\|TppWeatherManager\|TppCommand\.Weather\|EnvironmentDaemon\|WindManager\|GeoTrap.*\|TppTrapCheck.*\|PlayerTrap\|TppCoder` | M13 | Blocks of both maps, clock, weather, zones and traps (M13 G2-G6). |
| N10 | `Ph.*\|SimDaemon\|DesDaemon\|Geo\|GeoPathService\|GeoSearchObject\|GeoSearchService\|GkSightCheckParam\|GkConeSightCheckParam\|TppSightObstructionManager\|FxGeoMaterial\|GkTacticalService\|GkTacticalWorld` | M14 | Physics, shape queries, sight rays (M14 G2). |
| N11 | `TppEquip\|TppBullet\|TppDamage\|TppShell\|TppPickable\|TppSupportRequest\|CaptureCage\|CaptureCageMaterial\|Gk(Offense\|Defense)TargetData\|TppOffenseTargetData\|AmmoStockIndex\|IgnoreDamageActionFlag\|DamageMessageFlag\|HeadshotMessageFlag\|BulletGuardArmorMessageFlag\|DeadMessageFlag\|Neutralize(Type\|Cause\|FobCause)\|WearEquip\|MbInterrogate\|Gimmick\|TppPlaced\|TppCollection` | M15 | Weapons, damage, CQC, items, breakable gimmicks (M15 G1-G8). |
| N12 | `TppRouteAnimationCollector` | M16 | Route animation clip paths. |
| N13 | `Application\|PlatformConfiguration\|AssetConfiguration\|Installer\|Chunk\|SignIn\|NtDaemon\|TppSystemLua\|TppSystem\|TppSystemUtility\|GameConfig\|QuarkSystem\|GameCore` | M23 | Platform, install, config and dev services of the standalone runtime. |
| N14 | `TppHostage2\|Hostage.*\|TppBuddy.*\|Buddy.*\|EntryBuddyType\|TppUav\|TppSahelan2\|TppLiquid2\|TppVolgin2.*\|TppAnimalSystem\|TppAnimalId\|Vehicle.*\|Corpse.*` | M18 | Every other GameObject family (M18 G1-G4). |
| N15 | `Mission\|Checkpoint.*\|GameSequenceController\|TppGameSequence\|TppGameStatus\|TppGameMode\|TppMotherBase.*\|TppMbDev\|MbsDevelopedEquipType\|MotherBase.*\|Demo.*\|TppDemoUtility\|TppChallengeTask\|EventLog\|TppEventLog\|PlayRecord\|Trophy\|CyprusMissionController` | M19 | Missions, sequences, demos, Mother Base (M19 G2-G6). |
| N16 | `TppServerManager\|NclDaemon\|NetworkInfo\|InvitationManager\|RankingBordId\|RecordRanking\|Shop\|TppNetworkUtil\|SyncUniqueId\|Replay\|Fob.*\|Dlc.*\|PatchDlc` | M19 | Online, FOB and DLC: offline answers, as `runtime.online` does. |
| N17 | `Player.*\|TppSoldier2\|TppSoldier2CommonBlockController\|Soldier.*\|Enemy.*\|CpType\|CommandAi\|StateFlag\|Reinforce\|TppCommandPost2\|TppCombatLocatorProvider\|TppCoverPointProvider\|SyncRouteManager\|GsRoute\|Nav.*\|GameObject\|TppGameObject\|GameMessage\|ScriptUpdater\|Util\|IntervalRegulator\|GkEventTimerManager\|Fox\|foxde\|LUA_EXT_BIND_DEBUG_SUPPORT\|StringId\|Entity\|EntityClassDictionary\|TagContainerEntity\|.*TransformEntity\|TransformRTEntity\|DataIdentifier\|PathMapper\|File\|Script\|FoxFlagContainer\|FoxDataLinkCollector\|Game\|TppSimpleGameSequenceSystem\|TppDefaultParameter` | M17 | Player, Soldier2, CP, nav, GameObject dispatch and the Fox core the slice runs on. |

| Rule | Commands | Owner | Why |
|---|---|---|---|
| C1 | `AddDamage\|SetDisableDamage\|ChangeLifeState\|Recovery(All\|Life\|Stamina)\|SetMaxLife\|SetLife\|SetMaxPartsLife\|SetStopLife\|SetKill\|SetInvincibleMode\|SetEnemyDamageRate\|SetIgnoreDamageAction\|SetEverDown\|SetEnableDyingState\|SetDyingFireInfinity\|SetForceDyingFire\|DyingFireOnce\|StartDeadEffect` | M15 | Damage and life (M15 G3). |
| C2 | `RequestForceFulton\|SetFultonEnabled\|SetFultonLevel\|IsFultonCaptured\|SetToHeliRecoveredComplete\|SetBringPlayerAsPrisoner` | M15 | Fulton (M15 G5). |
| C3 | `ChangeEquipSlot\|SetEquipId\|GetCurrentEquipId\|SetMainWeapon\|SetWearEquip\|SetUnarmed\|SetVisibleSuppressor\|SetGunLightSwitch\|DisablePickupMainWeapon\|RegistGrenadeId` | M15 | Equipment (M15 G1 / G8). |
| C4 | `Call(Voice\|Monologue\|Conversation\|Radio\|SoundEffect\|Sound)\|SetVoiceType\|SetConversationList\|SetSaluteVoiceList\|SetSlowDeadSoundEffect\|SetSoundSwitchCyprusMask\|RegisterSpecialEngineSfx\|SetRotorSoundEnabled\|RequestRadio\|SetChatEnable\|SetDisableOccasionalChat\|SetRouteExcludeChat\|SetHumming\|SetLangType\|SetCpSirenType\|SetCpForceSiren` | M12 | Voice, radio, sound (M12 G1). |
| C5 | `SetMarkerEnabledCommand\|GetMarkerEnabled` | M12 | HUD markers (M12 G5). |
| C6 | `StoreToSVars\|RestoreFromSVars\|ReadyToStoreToSVars` | M19 | Saves (M19 G1). |

Handler families: the owner column of `cmd_handlers.tsv` is approximate (`~`); the family below is read from the command set [I].

| Rule | Handlers | Family | Owner | Why |
|---|---|---|---|---|
| H1 | `0x141356170` | Soldier2 | M17 | The slice's AI type (M9 built its route / phase logic, not the handler). |
| H2 | `0x140d5df30`, `0x140d6160b` | CommandPost2 | M17 | The slice's CP (phase, routes, reinforce). |
| H3 | `0x1411566a0` | Player2 core plugin | M17 | The slice's player. |
| H4 | `0x140e86d3e`, `0x140e85e10`, `0x140e867f1` | Hostage2 | M18 | Full cast. |
| H5 | `0x140dd56f0` | Heli2 (support heli) | M18 | Full cast (M18 G2). |
| H6 | `0x140b2b79d`, `0x140b305b0` | vehicles, convoys | M18 | Full cast (M18 G2). |
| H7 | `0x140e4d250`, `0x141807830` | Horse2, Horse2 for VR | M18 | Buddies (M18 G3). |
| H8 | `0x141706276` | WalkerGear2 | M18 | Full cast. |
| H9 | `0x140c3d880`, `0x140dd0580` | Bird, smart animals | M18 | Animals. |
| H10 | `0x1419a7020` | Uav | M18 | Full cast. |
| H11 | `0x141310f10`, `0x141311442` | security / gun cameras | M18 | Full cast. |
| H12 | `0x1418bb820`, `0x1418bc23e`, `0x14193a110`, `0x141860830`, `0x1419e2a50` | Sahelan2, its sequence AI, Parasite2, other bosses | M18 | Bosses (M18 G4). |
| H13 | `0x1417a47a4`, `0x141816239` | unidentified enemy families (anti-heli / landing routes; Mother Base mode) | M18 | Full cast; family named when its type is decoded. |
| H14 | `0x140d86540`, `0x140d86ed2` | corpses and fova state | M18 | Full cast. |

## Manifest [B G1 basic checks, B G4 rejections]
`mod.json` (or a `MANIFEST` dict in a Python mod):
```json
{"namespace": "morale", "version": "0.1.0", "api": "0.1", "kind": "python",
 "entry": "morale.py", "depends": ["vanilla"], "after": [], "before": []}
```

- `namespace`: `[a-z][a-z0-9_]{1,31}`, unique; `vanilla` and `engine` reserved.
- `api`: `major.minor` of the Mod API it was written for. **Strict during 0.x (D2, Luc 2026-11-04):** the minor must equal the engine's, otherwise the mod is refused with a message naming both versions; from 1.0 a mod loads when the major equals and its minor <= the engine's.
- `kind`: `python` or `lua`. **Python mods are trusted (D1, Luc 2026-11-04):** they run in the engine process with full access, for prototypes you write or have read yourself; never load a Python mod from an unknown source. Mods meant for sharing are Lua (sandboxed, below).
- `depends`: hard dependencies (missing -> refused); `after` / `before`: soft order constraints.
- Lua mods: `entry` is the Lua source file; a mod folder is `mod.json` + entry (`load_mod_dir(path)`).

## Rejections [B G4]
Every refusal raises a `ModError` subclass (`Engine\mods\registry.py`) whose message names the mod(s) and whose `mods` attribute lists their namespaces (sorted, for tests and tools). A refused set leaves the registries exactly as before the `load()` call: the loader undoes every register / override of the set (journal per `ModContext`).

| Refusal | Class | Detected | Message (example) |
|---|---|---|---|
| API version | `ManifestError` | manifest check, before ordering | `mod 'probe': written for Mod API 0.2, engine is Mod API 0.1 (0.x: major.minor must match)` |
| Bad / reserved namespace, unknown field, bad kind | `ManifestError` | manifest check | `mod 'vanilla': reserved namespace` |
| Missing dependency | `LoadOrderError` | order resolution | `mod 'probe': missing dependency 'absent'` |
| Load-order cycle | `LoadOrderError` | order resolution; the cycle itself is reported, not every mod blocked behind it | `load-order cycle: a -> b -> a (each needs the next loaded first)` |
| Key conflict (same key) | `Conflict` | `register` | `parameters: 'a.x' registered by 'a', again by 'b'` |
| Message id collision | `Conflict` | `ctx.message(name)`: StrCode32 of the namespaced name equals an id already registered (vanilla or another mod) | `messages: StrCode32 0x3EE65CAF of 'probe.m012bc0df' (mod 'probe') collides with 'OnScriptBlockStateTransition' (mod 'vanilla')` |
| Sandbox escape (Lua) | `SandboxError` | at the access: forbidden global, binary chunk, instruction budget | `mod 'probe': sandbox refused global 'os'` |
| Nondeterminism | `NondeterminismError` | double run with the same seed (`Engine\mods\determinism.py`) | `nondeterministic mod(s) 'clock': event 1 differs between two runs with seed 0` |

## Loader [B G1 order, B G4 rejections, B G5 load order]
`Engine\mods\loader.py`, `ModLoader(registries).load(mods)`:

1. Validate every manifest (namespace, API version, entry).
2. Resolve order: `vanilla` first; then a topological sort over `depends` + `after` + `before`, ties broken by namespace (stable, independent of the filesystem). Missing dependency or a cycle refuses the whole set with a precise error (table "Rejections").
3. For each mod in order: build a `ModContext(registries, manifest, seed)` and call the mod's `register(ctx)` (Lua mods: inside the sandbox). An error in any mod undoes the whole set and is re-raised naming that mod.
4. Conflicts: registering a key that exists raises `Conflict` (owner of the existing entry and the new one named). New string keys of non-vanilla mods must be namespaced (**D3, Luc 2026-11-04**: `<ns>.Name`, message names hashed as StrCode32 of `"<ns>.Name"`; an unprefixed key is refused); `ctx.message("<ns>.Name", value)` registers the id and refuses a collision with any registered id, vanilla or mod (G4).
5. Context services: `ctx.random` (a `random.Random` seeded from the loader seed and the namespace's StrCode32: same seed, same numbers, independent per mod), `ctx.emit(*event)` (owner-tagged runtime trace in `Registries.trace`, compared by the double run).
6. `ModLoader.order` and `Registries.dump_json()` are the load report.

## Load order [D, B G5]
The load order decides which override wins and in which order hooks run. It is a pure function of the set of manifests: the order the mods are passed in, the filesystem order and the run never change it (`test_m10_load_order.py`).

1. **Resolution** (`resolve_order`): `vanilla` first. Edges "X loads before Y": `Y.depends` contains X (X must be in the set or already loaded, else refused); `Y.after` contains X; `X.before` contains Y. `after` / `before` naming a mod that is not in the set are ignored (soft). Then Kahn's algorithm: of all mods whose predecessors are loaded, the one with the **smallest namespace** (Python string order, i.e. code points) loads next. No constraint between two mods -> namespace order. A cycle is refused ("Rejections").
2. **Later `load()` calls** into the same registries come after every mod already loaded (their `preloaded` namespaces satisfy dependencies).
3. **Overrides** (`ctx.override`, any kind): applied in load order. The entry's value / impl / owner are the **last loaded** mod's; `Entry.layers` holds every `(owner, value)` in load order. A layer that sets only `impl` keeps the previous value (and the reverse).
4. **Command chaining**: the last loaded handler is outermost; `next` calls the one loaded before it.
5. **Hooks** at one site: **before hooks in load order**, a before that returns `CANCEL` stops the later before hooks and the engine call; **after hooks in reverse load order** (the first loaded mod's after runs last, so it wraps the outermost), and every after hook runs, also on a cancelled call (`call.cancelled` set). Changes a before hook makes to `args` are seen by the before hooks loaded after it and by the engine call.
6. **Undo** of a refused set restores the exact pre-load entries (value, impl, owner, layers); the result is the same as never loading the set.
Checked (G5): two parameter overrides (`cp.rate.alert`) and two hooks on one site (`cp.phase_change`, `route.switch`) for each way to order a pair (namespace tie, `after`, `before`, `depends`, and a constraint against namespace order), every permutation of the input list, and two runs: the load order, `Registries.dump_json()`, the override layers, the hook call order, the parameter read through `params.param`, the m9_phase alert drain and the owner-tagged trace are byte-identical.

## Extension kinds [B G3 reference mods, one each]
| Kind | API | Engine hook point |
|---|---|---|
| New system | `ctx.register("updaters", "<ns>.Name", {priority}, impl=factory)` with lifecycle `OnAllocate / OnInitialize / OnUpdate / OnTerminate` | `UpdateService` vector (priority order, insertion sort, `Scheduler.md`) |
| Message listener / own message ids | `ctx.listen(name_or_id, fn)` (`fn(msg, bus)`, registry kind `listeners`), `ctx.message("<ns>.Name")` -> id | `MessageBus.register_from(reg)`: one bus listener that calls the mod listeners of the message's id in registration order (`Messages.md`) |
| New GameObject type + SendCommand handlers | `ctx.register("gameobject_types", index, {...}, impl=manager_factory)`; `ctx.register("commands", "<type>:<ns>.Cmd", ..., impl=fn)` | `GameObjectManager.register_from`, `TypeManager.command` |
| New `.fox2` class | `ctx.register("reflection_classes", "<ns>.Class", {super, version, hash, properties: [{name, type, container, arraysize}]})` | `TypeDB.register_from(reg)` adds every registry class it lacks (own properties; inherited ones come from `super`); `World(typedb).add` then types the mod DataSet's entities (`Entities.md`) |
| Parameter override | `ctx.override("parameters", name, value)`; layered by load order | `Registries.param` |
| Before / after hooks | `ctx.hook(site, before=fn, after=fn)`; a before hook may change the arguments or cancel (section "Hook sites") | `route.switch`, `cp.phase_change`, `command.dispatch` |
| SendCommand handler chaining | `ctx.override("commands", key, impl=fn)`: for kind `commands` the context wraps `fn(next, instance, args)`, `next(instance, args)` calls the previous impl (`KeyError` when there is none: vanilla descriptors have no impl until their milestone ports them) | `TypeManager.command` (handlers copied by `GameObjectManager.register_from`) |
| AI node insert / replace | `ctx.override("ai_tables", name, value=...)`: the vanilla table plus / minus entries (a step name in an unnamed slot of `route.steps`, an event type in `route.no_stop_events`) | `route_follow`, `cp_phase`, `realize` read their tables through `params.table` (`SoldierAI.md`) |
| Blackboard access | read-only `CpView` / `SoldierView` / `PlayerView` passed to hooks (section "Hook sites") | `cp_phase`, `route_follow`, `realize` records |
| Lua library | Lua mod: `mod.library("<ns>.Lib", {Fn = function ... end, ...})` registers `lua_libraries` `<ns>.Lib` (`{kind: "library", after_chunks: 0, members: {Fn: "mod"}, values: {}}`) and one `natives` entry `<ns>.Lib.Fn` per function; its impl calls the Lua function **in the mod's own sandbox** (`LuaSandbox.call`: budget and refusals apply; arguments and results as plain values) | `ScriptHost(mods=[...])` + `register_upto`: the game's Lua sees the table `<ns>.Lib` |

## Hook sites [D design 2026-11-04, B G3 implementation]
E42 answered by design, no RE; built with G3 (`Engine\mods\hooks.py`): what a mod can observe, change or cancel around a named engine call. Hooks are a registry kind `hooks` (added with G3; key = site name, value = the ordered list of `(owner, before?, after?)`), so they are dumped, owner-tagged and undone like every other registration.

**API.** `ctx.hook(site, before=None, after=None)`:

- `before(call) -> None | CANCEL`: `call` is a `HookCall` with `site`, `frame` (host frame counter), `args` (a mutable dict of the site's arguments, changes are passed on), `view` (read-only blackboard view, below), `cancelled` (bool). Returning `hooks.CANCEL` stops the call: later before hooks do not run, the engine function is not called, the result is the site's **cancel result**.
- `after(call, result) -> result`: sees the result (or the cancel result, `call.cancelled` set) and returns the result passed on (return it unchanged to observe only).
- Order: before hooks in load order, after hooks in reverse load order (the first loaded mod wraps the outermost), same order on every run (section "Load order"). A site with no hooks costs one registry lookup (section "Overhead budget").
- Lua mods: `mod.hook(site, before, after)` (either may be nil); each call runs through the sandbox's budget (`LuaSandbox.call`). `before(args, view)` gets plain tables (copies; `rec` as `{node, evt, step}`, float32 as numbers) and returns `mod.CANCEL`, a table (the changed `args`, read back key by key) or nil; `after(args, result)` returns the result or nil (unchanged).
- **Engine side**: `hooks.run_site(reg, site, args, call, cancel_result, view=None, frame=0)`; `reg` = the engine instance's registries (`None` = the compat default, which has no hooks). With an empty list the engine function is called directly, no `HookCall` is built. `call(args)` runs the engine function on the (possibly changed) arguments; `view` may be a callable (built only when a hook runs).
- Determinism: hook calls are part of the owner-tagged trace (`ctx.emit` from hooks, plus one `["hook", site, frame, cancelled]` event per call that a mod handled), so the G4 double run covers them.

**First sites** (each implemented by G3 with one reference mod):

| Site | Engine call | `args` | Result / cancel result | Reference mod (G3) |
|---|---|---|---|---|
| `route.switch` | `route_follow.step_after(..., soldier=, route_id=, frame=)` (a soldier's record moves to the next leg or node event); the caution / evasion route switch joins the site when it is ported | `soldier` (index), `route` (id), `rec` (node, evt, step), `reverse`, `pos` | new `Rec` / the current `Rec` (the soldier stays on its leg or event) | hook that cancels a route switch |
| `cp.phase_change` | `cp_phase.phase_change(cp, from_phase, to_phase, cause, timer, reg=, frame=, view=)` (every CP phase transition: fall-back on request finish, raise on notice) | `cp`, `from_phase`, `to_phase`, `cause` (request id or `"timer"`), `timer` (float32) | new phase / the old phase (timer untouched) | morale system observes phase changes (with its updater) |
| `command.dispatch` | `TypeManager.command` (also behind `send_command`) before the registered handler; the manager's `registries` is set by `GameObjectManager.register_from` | `type_index`, `instance`, `command` (name), `hash32`, `params` (the command table) | handler return value / `None` | chained handler logs and rewrites one command |

Handler chaining (`ctx.override("commands", key, impl=fn)`, `fn(next, instance, args)`) stays a separate kind: it replaces one handler, a `command.dispatch` hook sees every command of every type.

**Blackboard views** (read-only snapshots taken when the hook call starts, valid for that call only; frozen dataclasses, float32 fields as `np.float32`; Lua gets copies):

- `CpView`: `cp` (id), `name`, `phase`, `timer`, `rates` (by phase, from the registry), `requests` (pending request ids in order), `members` (soldier indices), `front_point` (x, y, z), `investigators` (soldier indices holding the investigate role).
- `SoldierView`: `index`, `cp`, `route` (id), `rec` (node, evt, step), `kind` (record +0x66 & 3), `flags`, `position`, `realized` (bool), `role`.
- `PlayerView`: `position`, `seen_by` (cp ids whose linger is above 0), `phase_known` (bool per cp).
Views never expose engine objects: a hook changes state only through `args`, its result, or registry calls of its own namespace.

## Reference mods [B G3]
`Engine\mods\reference\`, one per extension kind; `Engine\tests\test_m10_ref_mods.py`, fixture `Engine\tests\fixtures\m10_ref_mods.json` (one section per mod, generated by `Tools\m10_ref_fixture.py`, `--check` in the test; each section also holds what the test predicts independently). Every mod passes the G4 double run; loading them changes no other engine instance, and the null-mod / vanilla traces stay byte-identical.

| Mod | Kind(s) | What it does | Checked against |
|---|---|---|---|
| `morale` | new system (updater, lifecycle) + `cp.phase_change` after hook | morale per CP in 0..1000: per frame +1 sneak, 0 caution, -1 evasion, -2 alert (clamped); phase from the hook; `OnAllocate` / `OnInitialize` / `OnUpdate` / `OnTerminate`; emits every 60 frames | `m9_phase` phase changes replayed on the frame axis; final morale = closed form over the phase segments |
| `listener` | message listener + own message id | `ctx.message("listener.Rally")`; on `Finish` (sender `Timer`) raises `listener.Rally`; on `listener.Rally` emits | bus log `Finish`, `listener.Rally` in one drain |
| `beacon` | new GameObject type + SendCommand handlers | type 120 `beacon.Beacon` (group 1), commands `beacon.SetLevel` / `beacon.GetLevel` | `GameObjectManager` tick + `send_command` |
| `chain` | handler chaining + `command.dispatch` before hook | chained `beacon.SetLevel` clamps the level to <= 5; the dispatch hook logs every command and rewrites a negative level to 0 | results through both layers |
| `fox2cls` | new `.fox2` class | class `fox2cls.Beacon` (super `Data`; `level` uint32, `position` Vector3) and DataSet `reference\data\beacons.fox2` (3 entities, equal to the mod's builder output) | `World.add` types the 3 entities only with `TypeDB.register_from` |
| `alertrate` | parameter override | `cp.rate.alert` = float32(1/20) (x1.5) | `m9_phase`: alert drain from the clear timer 1798 frames (live) -> the predicted count; alert windows drain at the new rate, caution / evasion windows unchanged |
| `holdroute` | `route.switch` before hook (cancel) | cancels every switch of soldier 91 | `m9_route`: soldier 91 keeps its record, every other transition equals vanilla |
| `ainode` | AI node insert | names unnamed step slot 8 `ainode.LookAround`; inserts event type 0xEF94DD47 (the most common node event of the m9_route routes) into `route.no_stop_events` | `m9_route`: a transition differs from vanilla exactly when vanilla lands on that event type |
| `lualib` | Lua library (Lua mod, sandboxed) + Lua `cp.phase_change` hook | `lualib.Greeting` (`Add`, `Hello`, `Roll` seeded, `Escape` reads `os`) | `ScriptHost(mods=[lualib])`: game Lua calls the library; `Escape` is refused by the sandbox |

## Overhead budget [D, B G6]
The registry / hook path may cost at most **5 % frame time** against the pre-registry baseline on the M3 and M9 scenarios (`test_m10_perf.py`).

- **Registry path:** the engine instance's vanilla `Registries` passed as `reg`, no hooks registered: every frame reads its parameters, AI tables and message names through the registry and looks up each hook site it passes.
- **Baseline:** the same consumer code with the registry layer replaced by the module constants it is built from (`params.param` / `params.table` answer from dicts made by `vanilla.parameters()` / `vanilla.ai_tables()` without a `Registries`; `hooks.hooks_at` answers nothing and `hooks.run_site` calls the engine function directly), i.e. the code before G1. Both paths give byte-identical results (checked in the same test).
- **Workloads:** M9 = the two `m9_phase` runs frame by frame (phase changes through `cp.phase_change`, one `cp_phase.rate` read + float32 drain step per frame; ~27,000 frames) and every `m9_route` transition through `route.switch` (2,035 calls). M3 = the live updater-vector change sequence (9 frames) and the 43-message sequence, priorities and names read per use, repeated 40 times. Load time (building the registries, loading mods) is not frame time and is not in the budget.
- **Measurement** (test code only; no engine module reads a clock): fixtures loaded and instances built outside the timed region; 2 warm-up rounds; 15 alternated pairs (A B, B A, ...) with the garbage collector off; ratio = median of the per-pair ratios; up to 3 attempts, each a full median, the best one counts (noise only ever slows one attempt; a real regression fails all three). Measured 2026-11-05: M9 1.005-1.018, M3 1.009-1.032.
- **Read path that keeps it:** each `Registry` keeps `live` (key -> current value, written by register / override / remove / undo) for frame-time reads (`Registry.get`, `params.table`), and `decoded` (`params.param`'s float32 values decoded once from `bits`; every write to the key drops its line). Before this cache `params.param` rebuilt the float32 on every read and the M9 path cost 2.1x the baseline.
- With hooks registered a site costs what the hooks do (a `HookCall` and a view per call); that is the mod's cost, not the API's.

## Sandbox (Lua mods) [B G4]
`Engine\mods\lua_mod.py`. Each Lua mod gets its own Lua 5.1 state (lupa, as the M4 host) and an environment table with only copies of `string` (no `dump`), `table`, `math` (`math.random` / `math.randomseed` replaced by the mod's `ctx.random`), and `assert`, `error`, `ipairs`, `next`, `pairs`, `pcall`, `select`, `tonumber`, `tostring`, `type`, `unpack`, `setmetatable`, `getmetatable`, plus `loadstring` (text only; the chunk gets the sandbox environment) and the read-only API table `mod`: `namespace`, `register(kind, key, value)`, `override(kind, key, value)`, `message(name, value)` -> id, `param(name)`, `random(m, n)`, `emit(...)`. The entry chunk is the registration: it runs once inside `register(ctx)`.

- **Refused globals** (reading one raises `SandboxError` naming the global and the mod): `os`, `io`, `debug`, `require`, `package`, `module`, `load`, `loadfile`, `dofile`, `collectgarbage`, `rawset`, `rawget`, `rawequal`, `setfenv`, `getfenv`, `newproxy`, `gcinfo`, `coroutine`, `_G`. Other unknown globals read as nil (Lua semantics).
- **Binary chunks**: an entry or `loadstring` text whose first byte is `\27` is refused before Lua sees it.
- **Instruction budget** (E43 answered, design): a count hook set from outside the sandbox stops any single call into the mod after `LUA_BUDGET` = 10,000,000 VM instructions (`SandboxError ... instruction budget`); the hook lives on the engine side, so the mod cannot clear it (`debug` is refused).
- The API table is a proxy: writes raise and its metatable is locked. Lua tables passed to `register` become JSON-able Python values (sequences -> lists, maps -> dicts with sorted keys, integral numbers -> int).

## Determinism [D, B G4 double run, B C4]
- Randomness only from the engine's seeded generator (the game's own generator from M13); mods get it through the context (`ctx.random`, Lua `math.random`), never `random` / `math.random` directly.
- No wall clock: mods see the frame counter and the host clock (1/60 s per frame). Lua mods cannot reach a clock (`os` refused); Python mods are trusted (D1) and are checked by the double run.
- Registration order, iteration order and dump order follow the resolved load order; no hash-set iteration anywhere in the registry.
- **Double run** (`Engine\mods\determinism.py`, G4): `double_run(make_mods, frames, seed)` builds a fresh vanilla `Registries` twice, loads the mods, runs `frames` scheduler frames over the mods' updaters and compares the owner-tagged trace: every mod registry entry and override layer (owner, kind, key, value) plus every `ctx.emit` event. Any difference raises `NondeterminismError` naming each mod whose part differs (sorted) and its first differing event.
- **C4 (2026-11-05, `Engine/tests/test_determinism.py`):** every M10 scenario (null mod: M3, M4 f30010, M9 traces and a double run; the nine reference mods through their G3 scenarios, hooks at all three sites included; the seven G5 load-order cases in input order and reversed) runs twice in fresh instances and once more in a fresh Python process with another `PYTHONHASHSEED`; the scenario result, the owner-tagged trace and the registry dump of every `Registries` it built are byte-identical. Controls: a mod drawing from `ctx.random` with seed 0 vs 1 is caught (in process and across processes, only that mod named), a mod with hidden module state is caught by `double_run`. The process-wide compat default (`params.default_registries`, built lazily) is not a scenario instance and stays vanilla-only. Found and fixed: `ScriptHost.coverage()["stubs"]` broke call-count ties by set order (varied with `PYTHONHASHSEED`); ties now sort by name.

## Null mod [B G2]
`Engine\mods\reference\null.py`: namespace `null`, depends on `vanilla`, `register(ctx)` does nothing (no entry, no override, no hook, no listener). With it loaded the M3, M4 and M9 scenario traces are byte-identical to vanilla alone (`test_m10_null_mod.py`): M3 = updater vector replay and message sequence fed from the registry; M4 = the f30010 scenario and the f30020 gate-b scenario with delivery on the script host (call log, loads, errors, sequence); M9 = route step machine and CP phase drain fed from the registry's parameters and AI tables. The only allowed difference is the load report itself (`Registries.loaded`, `ModLoader.order`).

## Extension points
This document is the extension-point index; each subsystem spec names its own:

- `Scheduler.md`: updaters (priority, lifecycle), GameObject type slots and update groups.
- `Messages.md`: message ids (namespaced StrCode32), listeners, SendCommand handlers and chaining.
- `Entities.md` / `Reflection.md`: reflection classes, `.fox2` classes from mod DataSets.
- `ScriptHost.md`: Lua libraries, natives, Lua mod sandbox.
- `Resources.md`: resource loaders by extension, packages from mods.
- `World.md`: stage-block and identifier data from mods.
- `Navigation.md`: nav worlds and path queries (MOD-D).
- `SoldierAI.md`: phase rates, radio types, member roles, route step table, realize budget.

## Evidence
- Vanilla tables registered from: `Engine\tests\fixtures\m4_lua_bindings.json` (Lua libraries), `m3_frame_trace.json` (updater vector, type update groups), `mgsv_unified_server\data\re\gameobject_type_index.tsv` and `cmd_handlers.tsv` (copied into `Engine\mods\vanilla\*.json`), `fox_edb.json` (reflection), constants of `Engine\runtime\*` and `Engine\world\*`.
- `Engine\tests\test_m10_null_mod.py` (G2): null-mod traces byte-identical to no mod (M3 / M4 / M9).
- `Engine\tests\test_m10_rejects.py` (G4): every row of "Rejections" with a real case; the message-id collisions are genuine StrCode32 collisions found by brute force (`probe.m012bc0df` = `OnScriptBlockStateTransition` 0x3EE65CAF, `probe.m024070d7` = `Start` 0xC6670D02, `alpha.m0ca75` = `beta.m02356` 0x69DF8779), each hash recomputed in the test.
- `Engine\tests\test_m10_consumers.py` (G1): consumers read the registry; vanilla values bit-identical to the constants; an override changes only its instance.
- `Engine\tests\test_m10_registry.py` (G1): every registry dump equals the table it came from; two builds give byte-identical dumps; the script host installs Lua libraries and natives only through the registry; M0-M9 gate test files unchanged against `verifiers.lock.json`.

## Open (OPEN_QUESTIONS.md E42-E45; decisions D1-D3 confirmed by Luc 2026-11-04)
- Hook sites: built with G3 at `route.switch` (step_after), `cp.phase_change`, `command.dispatch`; the caution / evasion route switch joins `route.switch` when it is ported. Live order of a mod listener relative to the mission `OnUpdate` stays E45.
- Overhead with hooks registered is not budgeted (section "Overhead budget"); a native (C++) hot path for registry reads is not needed at M10 (registry path within 2 % on M9).

---
<small>Source: `docs/engine/ModAPI.md` in the project repository &middot; generated 2026-11-05.</small>
