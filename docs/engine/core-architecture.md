# Core architecture notes (2026-10-19)

Milestones 1-3 (FoxRe agent, reviewed 2026-10-19). Trust only claims tagged [V]; review banners mark wrong [x] claims. Merged 2026-10-21 from: `ENGINE.md`, `ENGINE.md`, `ENGINE.md`.

---

# Milestone 1 Investigation Report: Fox Engine Core Spine, Startup Lifecycle, and Class Registry (`QuarkSystemTable` / `ClassDescriptor` / `GameObjectManager`)

> **Review 2026-10-19:** boot chain, 0x140BFF050 (11,344 sites) and 0x140BFF070 (1,506 sites) [V]; Quark slot names [I]; "Sahelan SendCommand 0x1418B9CE0" is wrong [x] (verified handler 0x1418BB820). Details: `mgsv_unified_server/docs/FOXRE_REVIEW.md`.

**Investigator:** Investigation Worker (Open Fox Engine Project)  
**Binary Target:** *Metal Gear Solid V: The Phantom Pain* (PC Steam v1.0.15.4 EN, base `0x140000000`, `mgsvtpp.exe`)  
**Knowledge DB Status:** Verified connected (202.3 MB SQLite database, 143,899 functions, 9,146 class vtables, 173,985 hashes, 380 SendCommand IDs). Background sync idle, 0 stale sources.

---

## 1. Executive Summary

Milestone 1 reverse-engineers the foundational spine of Konami's Fox Engine. Through disassembly, decompile analysis, and comprehensive x64 cross-reference scanning across all 11,344 call sites, we have decoded:

1. **The Engine Startup Lifecycle:** From WinMain (`0x140003aa0`) to kernel initialization (`0x1400017c0`), registering the 12 top-level engine packages (`TppSystem`, `FoxQuark`, `GameCore`, etc.), triggering the subsystem cascade (`0x140bff180`), and entering the master frame update loop (`0x140064560` / `0x140001cb0`).
2. **The Global Class Registry Singleton:** Backed by global pointer `_DAT_142c3a8a0` (allocated in `0x140bfefa0`), registered by `0x140bff070`, accessed by `0x140bff050`, featuring vtable `0x142308648` and an array of 2,048 (`0x800`) `ClassDescriptor` slots.
3. **The `ClassDescriptor` ABI Specification:** A standardized 10-slot virtual table enabling engine-wide dynamic instantiation (`CreateInstance` allocating via Quark memory `0x140bff0e0`), component dependency resolution (`SetupSystem` querying `QuarkSystemTable + 0x00`), teardown (`TeardownSystem`), and interface querying (`QueryInterface` via 48-bit `StrCode64`).
4. **The Complete `QuarkSystemTable` Map:** All 25 active manager slots accessed across 11,344 call sites have been mapped with concrete offsets, caller counts, vtables, and subsystem roles (Memory, MessageBus, Collision/Target, Global Context, Spatial/Noise, etc.).
5. **The `GameObject` Architecture & `SendCommand` Pipeline:** Singleton `_DAT_142c389a0` (`GameObjectManager`), 16-bit ID bit-packing `(typeIndex << 9) | instanceIndex`, type lookup `0x140bf3fc0`, and `GameObject.SendCommand` (`0x140bfa380`) dispatching to `manager->vtable[16]` (`+0x80`).

---

## 2. Engine Startup Lifecycle & Dependency Graph

### 2.1 The Entrypoint Chain
1. **WinMain (`0x140003aa0`):**
   - Parses command-line arguments using `GetCommandLineW()` and `CommandLineToArgvW()`.
   - Initializes core application arguments via `FUN_1400632b0(app_ctx, argc, argv)`.
   - Invokes engine initialization: `uVar3 = FUN_1400017c0();` (returns Application singleton `0x142b59100`).
   - Calls `FUN_140064560(app_singleton, app_ctx);` which runs the master engine frame loop.

2. **Master Kernel & Module Initialization (`0x1400017c0`):**
   - Sets global default parameters at `0x142b58ff0` keyed by `StrCode64("Default")` (`0x797fce5df5f8`).
   - Instantiates the Application object (`0x142b59100`) with vtable `0x1420a0930`.
   - Registers the **12 Top-Level Engine Packages** via sequential calls to `FUN_1400214b0()`:
     1. `0x14052e520`: `TppSystem` (Declares dependencies: `FoxKernel`, `FoxCore`, `Fio`, `Anim`, `Animx`, `FoxGameKit`, `Gr`, `Grx`, `Geo`, `Graph`, `Graphx`, `Nav`, `Navx`, `Nt`, `Nio`, `Tactical`, `Fx`, `Ui`, `Demo`)
     2. `0x14096f210`: `TppSound` (depends on `TppSystem`)
     3. `0x14051d260`: `TppMotherBaseCore` (depends on `TppSystem`, `TppGameKit`, `TppNetwork`)
     4. `0x140be4e70`: `TppMotherBaseStage` (depends on `TppMotherBaseCore`)
     5. `0x1406a77f0`: `TppEffect` (depends on `TppSystem`)
     6. `0x1407ce490`: `TppNetwork` (depends on `TppSystem`)
     7. `0x140555920`: `TppGameKit` (depends on `FoxQuark`, `TppNetwork`, `TppSystem`)
     8. `0x14085a6e0`: `TppUi` (depends on `TppSystem`, `TppNetwork`)
     9. `0x140bf1510`: `FoxQuark` (depends on `FoxKernel`, `FoxCore`)
     10. `0x140bf3620`: `GameCore` (depends on `FoxKernel`, `FoxCore`, `Nt`)
     11. `0x1409909c0`: `TppPhysics / GeoBridge`
     12. `0x1405132f0`: `GameService` (depends on `FoxKernel`, `FoxCore`, `Graphx`, `frt`)
   - Calls `FUN_140bff180()`, triggering the subsystem registration cascade across `0x140c03200` to `0x140c8cb50`.

3. **Master Engine Frame Loop (`0x140064560`):**
   ```c
   while (cVar2 == '\0') {
     uStack_18 = 0xffffffffffffffff;
     FUN_14007f840(param_1 + 0xc, &uStack_18);
     func_0x000140084570(); // Windows Message Pump (PeekMessage/DispatchMessage)
     (**(code **)(*param_1 + 0x48))(param_1, &uStack_18); // Application::vtable[9] (+0x48)
     FUN_140064030(param_1, &uStack_18);
     cVar2 = FUN_14001ff70(param_1);
   }
   ```
   - `Application::vtable[9]` (`+0x48`) resolves to `0x140001cb0` (`MasterFrameUpdate`).
   - `0x140001cb0` executes the per-frame scheduler across GameObject actors, physics, animation, and message queues.

---

## 3. The Global Class Registry Architecture (`_DAT_142c3a8a0`)

All class descriptors across the engine register into a single global repository singleton located at `_DAT_142c3a8a0`.

### 3.1 Singleton Accessor & Allocator (`0x140BFEFA0`)
```c
undefined8 * FUN_140bfefa0(void) {
  if (_DAT_142c3a8a0 == NULL) {
    _DAT_142c3a8a0 = (undefined8 *)func_0x0001400041a0(0x4018); // Heap alloc 16,408 bytes
    if (_DAT_142c3a8a0 != NULL) {
      *_DAT_142c3a8a0 = &UNK_142308648;                     // Registry Vtable
      _DAT_142c3a8a0[1] = 0;                                // +0x08: pQuarkSystemTable (initially NULL)
      *(uint32_t *)(_DAT_142c3a8a0 + 2) = 0;                // +0x10: registered_count = 0
      // Clears array of 0x800 (2048) descriptor pointers starting at +0x18
      memset(_DAT_142c3a8a0 + 3, 0, 0x100 * 8 * 8); 
    }
  }
  return _DAT_142c3a8a0;
}
```

### 3.2 Registry Memory Layout (`_DAT_142c3a8a0`)
| Offset | Type | Field Name | Description |
|---|---|---|---|
| `+0x00` | `void*` | `vtable` | Points to `0x142308648` (Registry Vtable) |
| `+0x08` | `void*` | `pQuarkSystemTable` | Pointer to global `QuarkSystemTable` (returned by `0x140BFF050`) |
| `+0x10` | `uint32_t` | `registeredCount` | Number of registered class descriptors (currently 1,491) |
| `+0x14` | `uint32_t` | `padding` | Alignment padding |
| `+0x18` | `ClassDescriptor*[2048]` | `descriptors` | Array of 2,048 class descriptor pointers (`0x18 + i*8`) |

### 3.3 Registry Vtable (`0x142308648`)
- **Slot 0 (`+0x00`) — `0x140bfef30`:** `~ClassRegistry()` (Destructor).
- **Slot 1 (`+0x08`) — `0x140c0e770`:** `SetQuarkSystemTable(void* pTable)`:
  ```c
  void SetQuarkSystemTable(ClassRegistry* this, void* pTable) {
    this->pQuarkSystemTable = pTable; // *(this + 8) = pTable;
  }
  ```

- **Slot 2 (`+0x10`) — `0x1407d9020`:** `GetRegisteredCount()`: Returns `this->registeredCount` (`*(uint32_t*)(this + 0x10)`).
- **Slot 3 (`+0x18`) — `0x140bfef70`:** `ExportRegisteredClasses(ClassDescriptor** outArray)`:
  Copies all pointers from `this->descriptors` into `outArray`.

### 3.4 Key Global API Entrypoints
- **`0x140BFF050()` — `Fox_GetQuarkSystemTable()`:**
  ```assembly
  0x140bff050: sub rsp, 0x28
  0x140bff054: call 0x140bfefa0      ; Get registry singleton
  0x140bff059: mov rax, [rax + 8]    ; rax = registry->pQuarkSystemTable
  0x140bff05d: add rsp, 0x28
  0x140bff061: ret
  ```

- **`0x140BFF070(ClassDescriptor* pDesc)` — `Fox_RegisterClassDescriptor()`:**
  ```assembly
  0x140bff070: push rbx
  0x140bff072: sub rsp, 0x20
  0x140bff076: mov rbx, rcx          ; rbx = ClassDescriptor*
  0x140bff079: call 0x140bfefa0      ; rax = registry
  0x140bff07e: test rbx, rbx
  0x140bff081: je 0x140bff096
  0x140bff083: mov edx, [rax + 0x10] ; edx = count
  0x140bff086: cmp edx, 0x800        ; cap at 2048
  0x140bff08c: jae 0x140bff096
  0x140bff08e: mov [rax + rdx*8 + 0x18], rbx ; registry->descriptors[count] = pDesc
  0x140bff093: inc dword ptr [rax + 0x10]    ; count++
  0x140bff096: add rsp, 0x20
  0x140bff09a: pop rbx
  0x140bff09b: ret
  ```

---

## 4. `ClassDescriptor` Specification

Every runtime gameplay class, actor manager, and component controller registers a static descriptor instance via its CRT initializer before `main()` executes.

### 4.1 In-Memory Object Layout
| Offset | Type | Field Name | Description |
|---|---|---|---|
| `+0x00` | `void*` | `vtable` | Pointer to class-specific descriptor vtable |
| `+0x08` | `uint64_t` | `classHash` | 48-bit `StrCode64` hash of the class name |
| `+0x10` | `uint64_t` | `flags / chain` | Initialization flags / linked list pointer |

### 4.2 Standard Static Initializer Pattern
Disassembly of caller `0x142009660` (`TppUiMenuTitleCallback`):
```assembly
0x142009660: sub rsp, 0x38
0x142009664: mov qword ptr [rsp + 0x20], -2
0x14200966d: lea rax, [rip + 0x300a9c]     ; rax = Descriptor Vtable (0x14230a110)
0x142009674: mov [rip + 0xa8f275], rax     ; desc->vtable = 0x14230a110
0x14200967b: movabs rax, 0xc9e730521b42    ; StrCode64("TppUiMenuTitleCallback")
0x142009685: mov [rip + 0xa8f26c], rax     ; desc->classHash = 0xc9e730521b42
0x14200968c: mov qword ptr [rip + 0xa8f269], 0 ; desc->flags = 0
0x142009697: lea rcx, [rip + 0xa8f252]     ; rcx = &desc (0x142a988f0)
0x14200969e: call 0x140bff070              ; RegisterClassDescriptor(&desc)
```

### 4.3 Virtual Method Table Specification (10 Slots)
Using `TppBuddyDog2` descriptor vtable (`0x142315d68`) as the reference implementation:

| Slot | Disp | Function | Role | Implementation Details |
|---|---|---|---|---|
| **0** | `+0x00` | `0x140cc0b30` | `~ClassDescriptor()` | Destructor. Restores base vtable, frees dynamic data. |
| **1** | `+0x08` | `0x140c554c0` | `CreateInstance()` | **Factory constructor:** Allocates `0x218` bytes (instance size) with 16-byte alignment via `0x140bff0e0` (`QuarkSystemTable + 0x08` heap), invokes C++ constructor `0x140c55530`, returns instance pointer. |
| **2** | `+0x10` | `0x141777540` | `DestroyInstance(void* inst)` | **Destructor dispatcher:** Checks `inst != NULL`, invokes `(*inst->vtable)[0](inst, 1)` (deleting destructor). |
| **3** | `+0x18` | `0x140c553c0` | `PlacementConstruct(void* mem)` | Placement new; initializes object state at pre-allocated memory. |
| **4** | `+0x20` | `0x140c55bf0` | `SetupSystem(pSystem, pParams)` | **Component Binder:** Resolves all required actor controllers (`TppGameObjectInfo`, `TppGameObjectRealizerController`, `TppBuddyDog2NoticeController`, `TppNavigationController`, `TppAiController`, `TppDamageController`) via `QuarkSystemTable + 0x00` lookup. |
| **5** | `+0x28` | `0x140c58240` | `TeardownSystem(pSystem)` | **Component Unbinder:** Unregisters all bound component controllers from `QuarkSystemTable + 0x00` and frees subsystem buffers. |
| **6** | `+0x30` | `0x140c55a30` | `QueryInterface(uint64_t hash)` | Dynamic cast / interface query. Compares `rdx` against `0x0d6974413c33` (`StrCode64("TppBuddyDog2")`). If matched, returns adjusted interface pointer `rcx + 0x28`. |
| **7** | `+0x38` | `0x1400fe390` | `GetPropertyLayout() / GetFlags()` | Returns property flags or layout descriptor. |
| **8** | `+0x40` | `0x140c55990` | `GetDescriptorSingleton()` | Returns pointer to static `ClassDescriptor` singleton (`0x142a9ab70`). |
| **9** | `+0x48` | `0x140c55980` | `GetSuperClass() / GetTypeInfo()` | Returns superclass pointer from `[rcx + 0x1a0]`. |

### 4.4 Registered Class Breakdown
Analysis of all 1,506 callers of `0x140bff070` reveals **1,491 distinct class registrations**. 

- 319 hashes are fully resolved to vanilla symbols in `mgsv_knowledge.db`.
- Suffix clustering demonstrates that registered classes are **Gameplay Component Controllers and Actor Managers**, not passive data types:
  - `Controller`: 119 classes (e.g. `TppBuddyDog2ActionController`, `TppSahelan2AiController`, `TppPlayerSightManager`)
  - `Ai`: 56 classes (e.g. `TppSahelan2PhaseAlertAi`, `TppBuddyDog2CommandAi`)
  - `Plugin`: 13 classes (e.g. `TppSahelan2BladePlugin`, `S2GrenadePlugin`)
  - `Handler`: 7 classes (e.g. `TppBuddyDog2DamageHandler`, `TppHeli2DamageHandler`)
  - `Realizer`: 6 classes (e.g. `TppParasite2Realizer`, `TppGameObjectRealizer`)
  - `Collector`: 12 classes (e.g. `TppBuddyDog2StateCollector`)
  - `Info`: 12 classes (e.g. `TppBuddyDog2FlagInfo`, `TppAnimalFlagInfo`)

---

## 5. Comprehensive `QuarkSystemTable` Subsystem Map

By disassembling instructions following `call 0x140bff050` across all 11,344 call sites in `mgsvtpp.exe`, we identified **25 active manager slots**. Every single access performs `mov rcx, [rax + disp]` followed by `call [vtable + slot]`.

`QuarkSystemTable` is an array of 33 quadwords (`void* QuarkSystemTable[33]`). Below is the complete reverse-engineered architectural map:

| Slot | Disp | Call Sites | Subsystem Name | Primary Roles & Evidentiary Hashes |
|---|---|---|---|---|
| **0** | `+0x000` | 289 | `ComponentRegistry / ClassLookupService` | Master component locator. `Lookup(StrCode64 hash)` resolves component factories (`TppGameObjectRealizerController`, `TppAiController`, `TppNavigationController`, `TppDamageController`, `TppSahelan2CoreAi`). |
| **1** | `+0x008` | 272 | `FoxMemorySystem / HeapManager` | Global engine allocator. Accessed by `0x140bff0a0` (realloc), `0x140bff0e0` (`Allocate(size, align)`), `0x140bff120` (`Free(ptr)`), `0x140bff150`. |
| **3** | `+0x018` | 71 | `OffenseTargetRegistry / PowerDamageSystem` | Lookup for offensive combat damage sensors (`POWER`). |
| **4** | `+0x020` | 127 | `NetworkUiManager / OnlineSaveState` | Online synchronization, FOB security details (`mb_pf_detail_security_d_num`, `gvars`, `UI_common_online`). |
| **5** | `+0x028` | 362 | `GameObjectLifecycleManager / LifeService` | Actor state lifecycle (`SetMaxLife`, `Unrealize`, `Escape`, `SetCyprusMode`, `GetRidePlayer`). |
| **6** | `+0x030` | 8 | `SavedVarsManager / SVarsService` | State persistence (`RestoreFromSVars`, `ReadyToStoreToSVars`, `ChangeFova`). |
| **8** | `+0x040` | 169 | `TitleSaveDialogManager / SystemSaveService` | System save dialogs and quit handling (`dialog_delete_savedata`, `TitleMenuReady`, `dialog_game_quit`). |
| **9** | `+0x048` | 31 | `ActorRealizerManager / PauseSystem` | Manages realizer states for unique boss actors (`TppSahelan2`, `TppBuddyQuiet2`, `TppBossQuiet2`, `TppVolgin2forVr`). |
| **12** | `+0x060` | 1,078 | `MessageBus / EventDispatcher` | **Master Event Bus:** `vtable[8]` (`+0x40`) implements `RaiseMessage(uint32_t msgId, void* payload)`. Used for engine-wide Lua/C++ messages (`SahelanVulcunStopToHeli`, `SahelanAllDead`, `VehicleTrouble`). |
| **13** | `+0x068` | 16 | `TowerAttackAlertManager / ScriptedSceneRealizer` | Realization of scripted environmental objects (`TppSahelan2TowerAttackAlertAi`). |
| **14** | `+0x070` | 31 | `MeshEquipAttachmentManager` | Attachment of wearable items and headgear (`Sunglasses`, `Picture`, `MESH_ROOT`, `Equip01`, `MESH_eyemask_NC_NSW_IV`). |
| **15** | `+0x078` | 165 | `RouteAndAreaManager / DecoySystem` | Spatial routes and tactical decoy simulation (`TppSoldier2`, `TppCommandPost2ActionController`, `TppDecoySystem`, `Area`). |
| **16** | `+0x080` | 625 | `TppTargetManager / CollisionSystem` | Offense/defense BVH hit collision tree. Resolved via `*(*(Quark+0x80)+0x10)`. Provides offense factories `vt[0x08]` / `vt[0x20]`, setup `vt[0x10]`, and hit collectors `vt[0x30]`. |
| **17** | `+0x088` | 344 | `WormholeFobGimmickManager` | FOB gimmick and wormhole teleportation (`AbortFromWormhole`, `OutFromWormhole`, `TppSecurityCamera2`). |
| **18** | `+0x090` | 1 | `DebugProfilerSlot` | Engine internal timing / debug profiling hook. |
| **19** | `+0x098` | 6,738 | `MasterGameContext / GlobalFlagsManager` | **Largest singleton in the engine.** Sub-tables: `+0x10` Options/Settings (`IsOption...`), `+0xE8` Sight/Combat context, `+0xF8` Stage Clock / Weather / Time of Day, `+0x16F` Demo Mode flag. |
| **20** | `+0x0A0` | 34 | `NavigationSceneManager` | World navigation controller and navmesh binding (`TppNavigationController_SnapToNavmesh`, `MainScene`). |
| **21** | `+0x0A8` | 347 | `SpatialAudioNoticeManager / NoiseSystem` | Spatial sound perception. `+0xA8 -> +0x08` = `NoiseSystem` (`AddNoise = (*NoiseSystem)[0]`). Handles voice commands (`voice_cmd_quiet_aim_help`) and whistles. |
| **22** | `+0x0B0` | 67 | `BoneSkeletonDamageManager` | Skeletal joint hitboxes and side targeting (`SKL_000_WAIST`, `SKL_043_RTOE`, `ENEMY`, `FRIEND`). |
| **23** | `+0x0B8` | 5 | `PhysicsSolverConstraintManager` | Low-level rigid body / constraint solver manager. |
| **24** | `+0x0C0` | 36 | `SoundController / SoundService` | Native sound events and music trigger playback (`SoundControllerImpl_CallInternal`). |
| **26** | `+0x0D0` | 3 | `UserStorageService` | Savegame file I/O abstraction (`UserStorage`). |
| **28** | `+0x0E0` | 25 | `ShieldDefenseTargetManager` | Shield collision sensors (`RootDefenseTarget`, `TargetShieldLeft`, `TargetShieldFront`). |
| **29** | `+0x0E8` | 172 | `HudUiManager / LayoutService` | HUD layout and action prompt icons (`UI_hud_acticon_NG`, `TITLE_NORMAL_BG`, `UI_msnprp2_lyt_main_on`). |
| **32** | `+0x100` | 2 | `InputManager / VirtualPadService` | DirectInput / keyboard / mouse binding (`UI_DECIDE`, `UI_CANCEL`, `UI_KBD_RIGHT`, `UI_MOUSE_DECIDE`). |

---

## 6. The `GameObject` Architecture & `SendCommand` Pipeline

### 6.1 Master `GameObjectManager` (`_DAT_142c389a0`)
- Allocated in `0x140bf9060` (size `0x470` bytes) during `GameCore` initialization (`0x140bf3790`).
- Bound to FoxEngine GameObject service with class hash `0xc6b72750`.
- Vtable: `0x1423073c0`.
- Holds an array of 256 `GameObjectTypeRecord*` pointers starting at offset `+0x30` (`this + 0x30 + typeIndex * 8`).

### 6.2 16-Bit `GameObjectId` Bit-Packing
Every actor in MGSV has a 16-bit integer ID (`uint16_t`):
$$\text{GameObjectId} = (\text{typeIndex} \ll 9) \mid \text{instanceIndex}$$

- **High 7 bits (bits 9–15):** `typeIndex` (0 to 127). E.g., `0x00` = Player, `0x01` = CommandPost (`0x0200`), `0x02` = Soldier (`0x0400`), `0x13` = BuddyDog (`0x2600`), `0x15` = Sahelan (`0x2A00`).
- **Low 9 bits (bits 0–8):** `instanceIndex` (0 to 511).

### 6.3 Manager Resolution (`0x140BF3FC0`)
`GameObjectManager::vtable[4]` (`+0x20`) at `0x140bf99e0`:
```c
void* GameObjectManager::GetTypeManager(GameObjectManager* this, uint16_t gameObjectId) {
  uint32_t typeIndex = gameObjectId >> 9;
  GameObjectTypeRecord* record = this->typeRecords[typeIndex]; // *(this + 0x30 + typeIndex*8)
  if (record != NULL && record->pSubRecord != NULL) {
    return record->pSubRecord->pTypeManager;                   // *(record + 8 + 0x20)
  }
  return NULL;
}
```

### 6.4 `GameObject.SendCommand` Execution Chain (`0x140BFA380`)
When Lua invokes `GameObject.SendCommand(id, { id = "CommandName", ... })`:

1. Validates Lua arguments (table/number at index 1, table at index 2).
2. Extracts `gameObjectId = lua_tointeger(L, 1)`.
3. Calls `0x140bf3fc0(gameObjectId)`, resolving the specific type manager (e.g. `TppSahelan2Manager`).
4. Extracts string field `id` from parameter table (`lua_getfield(L, 2, "id")`).
5. Computes 32-bit hash: `commandId = CityHash64(id) & 0xFFFFFFFF` via `0x1400234f0`.
6. Executes virtual dispatch to `manager->vtable[16]` (`+0x80`):
   ```c
   return (*(manager->vtable + 0x80))(manager, L, gameObjectId & 0x1FF, commandId);
   ```
   - For `TppSahelan2` (type 21), slot `+0x80` invokes `0x1418b9ce0` (Sahelan SendCommand switch).
   - For `TppSoldier2` (type 2), slot `+0x80` invokes `0x141356170` (Soldier SendCommand switch).
   - For `CommandPost2` (type 1), slot `+0x80` invokes `0x140d5df30` (CP SendCommand switch).

---

## 7. The `.fox2` Dataset to Runtime Actor Bridge

1. **Dataset Representation:** Level datasets (`.fox2`) instantiate `GameObjectLocator` and `GameObject` entities.
   - `GameObjectLocator` carries spatial coordinates (`transform`), flags, and a string property `typeName` (e.g. `"TppBear"`, `"TppSoldier2"`, `"TppSahelan2"`).
2. **Hash Resolution:** Upon loading, Fox Engine computes the 48-bit `StrCode64` of `typeName`:
   $$\text{StrCode64}("TppBear") = \text{0x35f7b2706575}$$
   $$\text{StrCode64}("TppBuddyDog2") = \text{0x0d6974413c33}$$
   $$\text{StrCode64}("TppSahelan2") = \text{0x18037b588147}$$

3. **Descriptor Lookup:** The engine searches `_DAT_142c3a8a0->descriptors` for the matching `ClassDescriptor`.
4. **Actor Instantiation:**
   - Calls `ClassDescriptor::vtable[1]` (`CreateInstance()`) to allocate actor struct memory via `QuarkSystemTable + 0x08`.
   - Calls `ClassDescriptor::vtable[4]` (`SetupSystem()`) to query `QuarkSystemTable + 0x00` and bind all component controllers.
   - Allocates the next available instance index and registers the actor in `GameObjectManager`.

---

## 8. Remaining Questions & Gaps

1. **Unresolved Class Descriptor Names (1,172 hashes):**
   - 319 hashes are decoded, leaving 1,172 hashes in `0x140bff070`. Because these are internal C++ controller/plugin class names not serialized directly into `.fox2` files, dictionary lookup against asset strings yielded 0 new hits.
   - *Lead for next investigator:* Run `Tools\harvest_tokens.py` on Ghidra decompiles to harvest type names from debug strings and assertions, then brute-force against the 1,172 class hashes with `Tools\strcode_brute\bin\brute.exe`.
2. **`QuarkSystemTable` Creation Point:**
   - We proved that `QuarkSystemTable` is set into `_DAT_142c3a8a0 + 8` via `0x140c0e770` and that all access occurs through `0x140bff050`. The exact allocator for the 33-slot table itself appears in early stage boot before package loading; tracing the caller of `SetQuarkSystemTable` with the non-null pointer during cold start will reveal the root Quark constructor.
3. **Priorities for Milestone 2 (`.fox2` Reflection & Entity Deserialization):**
   - Trace `DataSet` deserialization in `FoxCore` / `FoxGameKit`.
   - Map `Entity`, `Data`, and `DataElement` vtables and property descriptor lists (`PropertyInfo` reflection array).
   - Trace how `GameObjectLocator` entities in `.fox2` invoke `GameObjectManager` to spawn active actors at map coordinates.

---
*Report delivered to parent coordinator (`b69bb361-5e59-4f93-b4b3-d2ea0677eef7`).*

---

# Fox Engine Internals: Milestone 2 — The Entity, Property & .fox2 Reflection System

> **Review 2026-10-19:** entity-header offsets disagree with FoxTool's reader [x]; unknown1/unknown2 meanings unproven [?]; navigation slot functions are real but live in vtables 0x1423A14E0 / 0x1423A1570 (not 0x1423A1610) [x]. Details: `mgsv_unified_server/docs/FOXRE_REVIEW.md`.

## Executive Summary

This investigation provides a comprehensive reverse engineering of the Fox Engine reflection, serialization, and actor instantiation architecture in *Metal Gear Solid V: The Phantom Pain* (`mgsvtpp.exe`, Steam build 1.0.15.4 EN).

A fundamental finding of this investigation is the existence of **two distinct, co-operating class systems** within the Fox Engine executable:

1. **Fox Core Reflection & Entity System** (`FUN_140074c90` / `FUN_14007d210`):
   - Manages static asset definition, serialization, and level composition (`.fox2` binary/XML datasets).
   - Contains 1,138 registered entity classes (e.g., `Entity`, `Data`, `DataSet`, `TransformData`, `GameObjectLocator`, `GameObject`).
   - Driven by `ClassDescriptor` structures registered with class hashes, property metadata reflection tables, and static inheritance pointers.
2. **Fox Quark / Gameplay Class Registry** (`0x140BFF070`):
   - Manages runtime actor controllers, AI behavior-tree nodes, action plugins, and gameplay daemons.
   - Contains 1,491 runtime class descriptors registered during static C++ initialization (`_initterm` execution in `0x142000000 - 0x142066000`).
   - Driven by 5-slot virtual method tables: `slot 0` (RTTI / `GetClassDescriptor`), `slot 1` (`CreateInstance`), `slot 2` (`DestroyInstance`), `slot 3` (`QueryInterface`), and `slot 4` (`SetupSystem`).

During this investigation, we bridged the vocabulary between these two systems, leveraging AI behavior-tree node table hashes, vehicle controllers, weapon action plugins, and entity class tokens to crack **456 brand new verified class descriptor hashes**, bringing the total resolved classes from an initial baseline of 319 (21.4%) up to **775 resolved classes (52.0%)** in `mgsv_unified_server/data/re/strcode_bruteforced.tsv`.

---

## 1. The .fox2 File Format & Deserialization Pipeline

### 1.1 File Extension Table Registration
Fox Engine registers its supported file formats in a global format registry table during engine initialization:

- **Registry Table Address**: `0x1429E3550`
- **Registration Function**: `FUN_1400403F0`
- **Global File Handler Container**: `_DAT_142b63b10`

The file format table binds extension string hashes (`.fdes`, `.fdmg`, `.fmdl`, `.fox2`, `.fpk`, `.fpkd`, `.geom`, `.lad`, `.nav2`, `.parts`, `.ph`, `.sdf`, `.sim`, `.tgt`, `.veh`) to their corresponding loader/deserializer factory callbacks.

### 1.2 Binary .fox2 Format Specification

> **[x] Superseded 2026-10-21:** this header/entity layout is wrong. Verified layout (round trip on all 44,994 DataSets): [`docs/formats/FOX2.md`](../formats/fox2.md).
A compiled `.fox2` file (`FOXB` format) represents a serialized `DataSet` object graph:

| Offset | Type | Field | Description |
|---|---|---|---|
| `0x00` | `char[4]` | `magic` | Magic header: `\xf2box` (`0x786f62f2`) or `FOXB` |
| `0x04` | `uint32_t` | `version` | Format revision version (e.g., `2` or `3`) |
| `0x08` | `uint32_t` | `flags` | Deserialization and endianness flags |
| `0x0C` | `uint32_t` | `entityCount` | Total number of `Entity` instances serialized in the file |
| `0x10` | `uint32_t` | `stringTableOffset` | Byte offset to the inline string literal table |
| `0x14` | `uint32_t` | `stringCount` | Total number of unique string literals |
| `0x18` | `uint32_t` | `dataBlockOffset` | Byte offset to the start of serialized entity data payloads |
| `0x1C` | `uint32_t` | `fileSize` | Total size of the `.fox2` binary file |

### 1.3 Entity Record Structure in Binary Stream
Each serialized entity within the payload block begins with an aligned entity descriptor:

1. `classHash` (`uint64_t`, 48-bit `StrCode64`): Identifies the Fox Core entity class (e.g., `0x89731475623d` -> `TppHeli2`, `0x42f7c0062453` -> `GameObjectLocator`).
2. `entityAddress` (`uint64_t`): File-local reference ID used to link `EntityPtr` and `EntityHandle` references across the graph.
3. `propertyCount` (`uint32_t`): Number of serialized properties belonging to this instance.
4. `properties[]`: Array of property tuples:
   - `nameHash` (`uint64_t`, `StrCode64`): Property key (e.g., `"name"`, `"dataSet"`, `"transform"`, `"typeName"`, `"parameters"`).
   - `type` (`uint8_t`): Property type enumeration index (see Section 2.2).
   - `containerType` (`uint8_t`): Scalar (`0`), Dynamic Array (`1`), StringMap (`2`).
   - `arraySize` (`uint16_t`): Element count if container.
   - `value`: Direct primitive value or relative offset to complex payload.

### 1.4 Deserialization Sequence in `mgsvtpp.exe`
1. **Root Instantiation**: The loader instantiates the root entity, always an instance of `DataSet` (size `0x128`, vtable `0x1420C29F0`).
2. **Entity Deserialization Loop**:
   - The engine iterates through `entityCount`.
   - For each entity record, `0x14007d210` queries the Core Class Registry by `classHash`.
   - The registered factory callback (`ClassDescriptor::vtable[1]`) allocates heap memory via `BlockHeapAlloc` (`0x1400dcb50`).
   - The entity vtable is installed, and property deserializers map stream values into the target object fields using `PropertyInfo::offset`.
3. **Registration in DataSet**:
   - Every deserialized `Data` instance is inserted into `DataSet::dataList` (a `Fox StringMap<Data*>` at offset `DataSet + 0x78`).
   - The key is `Data::name` (Fox String at `+0x30`), and `Data::dataSet` pointer at `+0x38` is back-linked to the root `DataSet`.

---

## 2. Entity / Data / DataElement Reflection System

### 2.1 Core Inheritance Hierarchy & Vtable Layouts

> **2026-10-21:** class sizes below are confirmed [V] by the game's own registry dump ([`docs/engine/Reflection.md`](reflection.md)); vtables/field meanings still [I].

```
Entity (size 0x30, vtable 0x1420BF158)
  │
  ├── Data (size 0x78, vtable 0x1420CE800)
  │     │
  │     ├── DataSet (size 0x128, vtable 0x1420C29F0)
  │     │
  │     ├── TransformData (vtable 0x1420CD980)
  │     │     │
  │     │     └── GameObjectLocator (size 0x150, vtable 0x142306AF0)
  │     │
  │     └── GameObject (size 0x98, vtable 0x1423070C0)
  │
  └── DataElement (size 0x38, vtable 0x1420C17E0)
```

#### Detailed Struct Memory Layouts:

##### `Entity` (`0x30` bytes):
- `+0x00`: `vtable` (`0x1420BF158`)
- `+0x08`: `uint32_t refCount`
- `+0x0C`: `uint16_t flags`
- `+0x0E`: `uint16_t classId`
- `+0x10`: `ClassDescriptor* classDesc` (pointer to Fox Core class descriptor)
- `+0x18`: `void* dynamicProperties` (optional dynamic property bucket)
- `+0x20..0x28`: Internal allocation flags & allocator handle

##### `Data` (`0x78` bytes, inherits `Entity`):
- `+0x00..+0x2F`: `Entity` base fields (vtable `0x1420CE800`)
- `+0x30`: `FoxString name` (StrCode64 hash + literal pointer)
- `+0x38`: `DataSet* dataSet` (pointer to owner DataSet)
- `+0x40`: `FoxPath referencePath` (relative package/dataset asset path)
- `+0x48`: `DataBody* dataBody` (runtime instantiated scene body pointer)
- `+0x50..0x77`: Hierarchy link pointers and flags

##### `DataSet` (`0x128` bytes, inherits `Data`):
- `+0x00..+0x77`: `Data` base fields (vtable `0x1420C29F0`)
- `+0x78`: `StringMap<Data*> dataList` (collection of all contained Data entities)
- `+0x98`: `Vector<EntityPtr> dynamicEntities`
- `+0xB8`: `FoxPath datasetPath`
- `+0xD0..0x127`: Level streaming state, stage bounds, and dependency handles

##### `TransformData` (inherits `Data`):
- `+0x00..+0x77`: `Data` base fields
- `+0x80`: `Vector4 translation` (`(x, y, z, w)`)
- `+0x90`: `Quaternion rotation` (`(x, y, z, w)`)
- `+0xA0`: `Vector4 scale` (`(sx, sy, sz, 1.0)`)
- `+0xB0`: `TransformEntity* parent`
- `+0xB8`: `Vector<TransformEntity*> children`
- `+0x100..0x12F`: 4x4 world transform matrix cache

##### `GameObjectLocator` (`0x150` bytes, inherits `TransformData`):
- `+0x00..+0x12F`: `TransformData` base fields (vtable `0x142306AF0`)
- `+0x130`: `FoxString typeName` (e.g., `"TppHeli2"`, `"TppSoldier2"`, `"TppHostage2"`)
- `+0x138`: `uint32_t groupId`
- `+0x13C`: `uint32_t locatorFlags`
- `+0x140`: `EntityPtr<GameObjectLocatorParameter> parameters`

##### `GameObject` (`0x98` bytes, inherits `Data`):
- `+0x00..+0x6F`: `Data` base fields (vtable `0x1423070C0`)
- `+0x70`: `FoxString typeName`
- `+0x78`: `uint32_t groupId`
- `+0x7C`: `uint32_t totalCount` (maximum pool allocation capacity)
- `+0x80`: `uint32_t realizedCount` (active spawned count in scene)
- `+0x88`: `uint32_t flags`
- `+0x90`: `EntityPtr<GameObjectParameter> parameters`

### 2.2 Property Types & Type System
Fox Engine's property system identifies types via an internal 8-bit enumeration:

| ID | Type Name | C++ Type | Storage Size | Serialization Format |
|---|---|---|---|---|
| `0x01` | `Int8` | `int8_t` | 1 byte | Direct byte |
| `0x02` | `UInt8` | `uint8_t` | 1 byte | Direct byte |
| `0x03` | `Int16` | `int16_t` | 2 bytes | Direct 16-bit little-endian |
| `0x04` | `UInt16` | `uint16_t` | 2 bytes | Direct 16-bit little-endian |
| `0x05` | `Int32` | `int32_t` | 4 bytes | Direct 32-bit little-endian |
| `0x06` | `UInt32` | `uint32_t` | 4 bytes | Direct 32-bit little-endian |
| `0x07` | `Int64` | `int64_t` | 8 bytes | Direct 64-bit little-endian |
| `0x08` | `UInt64` | `uint64_t` | 8 bytes | Direct 64-bit little-endian |
| `0x09` | `Float` | `float` | 4 bytes | IEEE-754 32-bit float |
| `0x0A` | `Double` | `double` | 8 bytes | IEEE-754 64-bit double |
| `0x0B` | `Bool` | `bool` | 1 byte | 0 or 1 |
| `0x0C` | `String` | `FoxString` | 8 bytes | 48-bit StrCode64 hash |
| `0x0D` | `Path` | `FoxPath` | 8 bytes | 48-bit Path StrCode64 hash |
| `0x0E` | `EntityPtr` | `Entity*` | 8 bytes | Graph reference address |
| `0x0F` | `Vector3` | `float[4]` | 16 bytes | 128-bit aligned vector |
| `0x10` | `Vector4` | `float[4]` | 16 bytes | 128-bit aligned vector |
| `0x11` | `Quat` | `float[4]` | 16 bytes | 128-bit aligned quaternion |
| `0x12` | `Matrix3` | `float[12]` | 48 bytes | 3x4 rotation basis |
| `0x13` | `Matrix4` | `float[16]` | 64 bytes | 4x4 transform matrix |
| `0x14` | `Color` | `float[4]` | 16 bytes | RGBA normalized float |
| `0x15` | `FilePtr` | `FoxFilePtr` | 16 bytes | Path hash + archive handle |
| `0x16` | `EntityHandle` | `EntityHandle` | 8 bytes | Weak reference handle |
| `0x17` | `EntityLink` | `EntityLink` | 24 bytes | Archive path + dataset path + entity address |

### 2.3 RTTI & Dynamic Cast (`IsInstanceOf<T>`)
Fox Engine entities do not use Microsoft C++ `/GR` RTTI. Instead, dynamic casting is executed via the `ClassDescriptor` tree:

1. `entity->vtable[0]` is invoked to obtain `ClassDescriptor* current = entity->GetClass()`.
2. The casting function inspects `current->classHash` against target class hash.
3. If they do not match, the traversal follows `current = current->superClass` (stored at offset `ClassDescriptor + 0x48`).
4. Traversal terminates when a match is found (returning valid pointer) or when `current == NULL` (returning `nullptr`).

---

## 3. The Actor Instantiation Bridge (From .fox2 to Live Scene)

The bridge from a static level `.fox2` definition to an active gameplay actor executing in the Havok/Fox simulation proceeds across 4 rigorously verified stages in `mgsvtpp.exe`:

```
┌───────────────────────────────┐
│       DataSet (.fox2)         │
│ Contains: GameObjectLocator   │
│  (typeName: "TppHeli2", ...)  │
└───────────────┬───────────────┘
                │ Stage Load (Traverse Data Entities)
                ▼
┌───────────────────────────────┐
│ GameObjectLocator::slot 9     │ (0x140BF7710)
│ Allocates 0x90-byte Body      │
└───────────────┬───────────────┘
                │ Returns Body (vtable 0x142306B70)
                ▼
┌───────────────────────────────┐
│ GameObjectLocatorBody::slot 6 │ (0x140BF7980 -> thunk 0x140BF7D00)
│ 1. Extracts typeName & Matrix │
│ 2. Allocates CreationRequest  │
│ 3. Enqueues to GameObjectMgr  │
└───────────────┬───────────────┘
                │ GameObjectManager::vtable[2] (0x140BF8F80)
                ▼
┌───────────────────────────────┐
│ GameObjectManager Dispatcher  │ (0x140BF4690)
│ 1. Resolves typeIndex (0..127)│
│ 2. Allocates instance (0..511)│
│ 3. ActorID = (type<<9)|inst   │
└───────────────┬───────────────┘
                │ Invoke Type Factory (0x140BFF070 descriptor)
                ▼
┌───────────────────────────────┐
│ Actor Instantiation & Setup   │
│ 1. vtable[1] (CreateInstance) │ (Memory allocated via QuarkSystem 0x140BFF0E0)
│ 2. vtable[4] (SetupSystem)    │ (Wires Realizer, AI, Nav, Action controllers)
└───────────────────────────────┘
```

### 3.1 Stage 1: DataBody Instantiation (`0x140BF7710`)
During stage loading, the engine separates static asset definitions (`Data`) from scene instances (`DataBody`). For `GameObjectLocator`, virtual method `slot 9` (`0x140BF7710`) is invoked:

- Verifies registration of `GameObjectLocatorBody` in the Core Reflection registry (`0x140074c90`).
- Calls `BlockHeapAlloc(size=0x90, align=0x10)` (`0x1400dcb50`).
- Installs `GameObjectLocatorBody` vtable (`0x142306B70`).
- Returns the allocated body pointer to the scene manager.

### 3.2 Stage 2: CreationRequest Dispatch (`thunk_FUN_140bf7d00`)
At scene activation, the scene manager invokes virtual method `slot 6` (`0x140BF7980`), which jumps directly to `0x140BF7D00`:

- **Disassembly Trace (`0x140bf7d00`)**:
  ```x86asm
  0x140bf7d3d: mov     rbp, rcx                     ; rbp = this (GameObjectLocatorBody)
  0x140bf7d40: call    0x1400dfaa0                  ; rsi = Data* (GameObjectLocator definition)
  0x140bf7d48: lea     rcx, [rax + 0x130]           ; rcx = &locator->typeName
  0x140bf7d4f: call    0x140028970                  ; IsEmpty(typeName)?
  0x140bf7d54: test    al, al
  0x140bf7d56: jne     0x140bf7e52                  ; Exit if empty
  0x140bf7d5c: call    0x140bf4470                  ; rbx = GameObjectTypeRegistry singleton
  0x140bf7d73: call    0x14001d630                  ; rax = StrCode64(typeName)
  0x140bf7d7e: call    qword ptr [rdi]              ; Verify typeName is registered in game
  0x140bf7d89: movaps  xmm6, [rsi + 0x100]          ; Load transform matrix row 0
  0x140bf7d90: movaps  xmm7, [rsi + 0x110]          ; Load transform matrix row 1
  0x140bf7d97: movaps  xmm8, [rsi + 0x120]          ; Load transform matrix row 2
  0x140bf7d9f: mov     ecx, 0x50
  0x140bf7da4: call    0x140bf3c00                  ; Allocate 0x50-byte CreationRequest struct
  0x140bf7e08: mov     [rax + 0x30], typeNameHash   ; Store typeName hash
  0x140bf7e13: movaps  [rax], xmm6                  ; Store Transform row 0
  0x140bf7e16: movaps  [rax + 0x10], xmm7           ; Store Transform row 1
  0x140bf7e1a: movaps  [rax + 0x20], xmm8           ; Store Transform row 2
  0x140bf7e26: mov     [rax + 0x38], rsi            ; Store GameObjectLocator* pointer
  0x140bf7e38: mov     [rax + 0x40], parameters     ; Store parameters EntityPtr
  0x140bf7e3c: call    0x140bf9a10                  ; rax = GameObjectManager singleton
  0x140bf7e44: mov     rdx, creationRequest
  0x140bf7e4e: call    qword ptr [r8 + 0x10]        ; GameObjectManager::vtable[2] (0x140BF8F80)
  ```

- `GameObjectManager::vtable[2]` (`0x140BF8F80`) offsets `rcx` by `+0x430` to access the `CreationQueue` and calls `0x140BF90F0` to enqueue the actor for instantiation.

### 3.3 Stage 3: Actor ID Allocation & Type Index (`0x140BF4690`)
When `GameObjectManager` processes creation requests:

- Reads `typeIndex` from the registered Type Descriptor (stored at `typeDesc + 0x1C` as a 16-bit integer).
- Resolves against the canonical GameObject type index table (`exe 0x142A7BA90`, documented in `mgsv_unified_server/data/re/gameobject_type_index.tsv`):
  - `0`: `GAME_OBJECT_TYPE_PLAYER2`
  - `1`: `GAME_OBJECT_TYPE_COMMAND_POST2`
  - `2`: `GAME_OBJECT_TYPE_SOLDIER2`
  - `3`: `GAME_OBJECT_TYPE_HOSTAGE2`
  - `14`: `GAME_OBJECT_TYPE_HELI2`
  - `21`: `GAME_OBJECT_TYPE_SAHELAN2`
  - `24`: `GAME_OBJECT_TYPE_VOLGIN2`
- Allocates an instance index using a bitmap allocator (`0x140BF4690`):
  ```x86asm
  0x140bf46d4: movzx   eax, word ptr [rbx + 0x1c]   ; eax = typeIndex
  0x140bf46d8: mov     word ptr [rdi + 0x18], ax
  0x140bf46f4: mov     ebx, dword ptr [rdi + 0xc]   ; maxInstances for this type
  0x140bf4705: lea     rcx, [rbx + 7]
  0x140bf4709: shr     rcx, 3                       ; bitmap byte count = (maxInstances + 7) >> 3
  ```

- **16-bit Actor ID Encoding**:
  $$\text{ActorID} = (\text{typeIndex} \ll 9) \mid \text{instanceIndex}$$
  - `instanceIndex` (`bits 0..8`, range `0x000` to `0x1FF`, max 512 instances per type).
  - `typeIndex` (`bits 9..15`, range `0` to `127`, max 128 GameObject types).

### 3.4 Stage 4: Quark System Allocation & SetupSystem Wiring
With the unique Actor ID reserved:

1. **Memory Allocation**: The type manager queries the Quark class descriptor registered via `0x140BFF070` and calls `vtable[1]` (`CreateInstance`).
   - `CreateInstance` invokes `QuarkSystemTable[1]` (`0x140BFF0E0`), which allocates aligned actor memory from the gameplay slab allocator.
2. **SetupSystem Component Wiring**: The type manager invokes `vtable[4]` (`SetupSystem`), passing the actor pointer (`rsi`) and `CreationRequest*` (`rdi`).
   - `SetupSystem` queries `QuarkSystemTable[0]` (`ComponentRegistry`) via `StrCode64` hashes to look up all necessary controllers and behavior-tree nodes.

#### Concrete Trace: `TppHeli2` SetupSystem (`0x140DD42F0`)
Disassembly of `0x140DD42F0` reveals the exact wiring layout of `TppHeli2`:

- `0x140dd4337`: Queries `TppGameObjectInfo` (`0x7cffa68e663e`).
- `0x140dd4362`: Stores `TppHeli2Realizer` (`0xee21f8ab1680`) into `[rsi + 0x18]`.
- `0x140dd47b8`: Wires `TppGameObjectRealizerController` (`0x666e24552600`) into `[rsi + 0x1c0]`.
- `0x140dd47e7`: Wires `TppHeli2ActionController` (`0x919b5eef229c`) into `[rsi + 0x1c8]` and `[rsi + 0x60]`.
- `0x140dd4877`: Wires `TppNavigationController` (`0xa4872172cb1b`) into `[rsi + 0x1d0]` and queries sub-navigation interface `0xd08244349764`.
- `0x140dd48c5`: Computes `(typeIndex << 9)` into `bx`.
- `0x140dd523a`: Wires `TppHeli2CollisionController` (`0x1113dfb9f0ab`) into `[rsi + 0x108]` and `[rsi + 0x260]`.
- `0x140dd5298`: Wires `TppHeli2CustomizeController` (`0xcecdafe571fc`, newly cracked!) into `[rsi + 0x110]` and `[rsi + 0x268]`.
- `0x140dd5354`: Wires Flight/Control node (`0xb888d6cd3624`) into `[rsi + 0x120]` and `[rsi + 0x278]`.
- `0x140dd53b2`: Wires `TppHeli2MantisController` (`0x84dfdbd6fca6`) into `[rsi + 0x128]` and `[rsi + 0x280]`.
- `0x140dd53f0`: Wires `TppHeli2Parameters` (`0xa22027a0f9ca`).

---

## 4. Class Descriptor Translation Unit Clustering

The 1,491 class descriptors registered via `0x140BFF070` are spatialized in `.text` static initialization functions between `0x142000000` and `0x142066000`. By clustering the unresolved functions into 4KB blocks, we reveal that initializers are strictly partitioned by subsystem:

| VA Range | Primary Subsystem | Total Classes | Resolved | Samples of Cracked Classes |
|---|---|---|---|---|
| `0x142009000` | UI & Menus | 21 | 11 | `TppUiMenuTitleCallback`, `TppActiveSonar`, `TppTitleMenu` |
| `0x14200a000 - 0x14200b000` | Bear | 22 | 11 | `TppBearAttackAi`, `TppBearDamageAction`, `TppBearFultonAction`, `TppBearNormalAi` |
| `0x14200c000 - 0x142010000` | BuddyDog2 (D-Dog) | 79 | 45 | `TppBuddyDog2CommandAi`, `TppBuddyDog2Core`, `TppBuddyDog2FaceActionController`, `TppBuddyDog2TailActionController` |
| `0x142010000 - 0x142012000` | BuddyPuppy (D-Dog Puppy) | 42 | 33 | `TppBuddyPuppyFultonAction`, `TppBuddyPuppyFultonAi`, `TppBuddyPuppyPlayAi` |
| `0x142012000 - 0x142015000` | BuddyQuiet2 (Quiet) | 71 | 35 | `TppBuddyQuiet2CombatAi`, `TppBuddyQuiet2Core`, `TppBuddyQuiet2EquipController`, `TppBuddyQuiet2FacialPlugin` |
| `0x142015000 - 0x142016000` | Corpse & Dialogue | 32 | 15 | `TppSoldier2ConversationHandler`, `TppCorpse`, `TppCorpseActionController` |
| `0x142016000 - 0x142017000` | Damage System | 34 | 26 | `TppDamageController`, `TppDamageDaemon`, `TppDamageSystem` |
| `0x142017000 - 0x14201a000` | Heli2 (Support & Enemy Heli) | 83 | 44 | `TppHeli2FlightController`, `TppHeli2CustomizeController`, `TppHeli2AlphaController`, `TppHeli2SupportController` |
| `0x14201b000 - 0x14201d000` | Horse2 (D-Horse) | 42 | 18 | `TppHorse2ActionController`, `TppHorse2CoreAi`, `TppHorse2DamageAction`, `TppHorse2LifeController` |
| `0x14201d000 - 0x142020000` | Hostage2 | 88 | 34 | `TppHostage2CollisionController`, `TppHostage2Core`, `TppHostage2CoreAi`, `TppHostage2LifeController` |
| `0x142020000 - 0x142021000` | MbQuiet (Mother Base Quiet) | 31 | 13 | `TppMbQuiet`, `TppMbQuietActionCore`, `TppMbQuietCore` |
| `0x142021000 - 0x142022000` | Navigation & Noise | 34 | 9 | `TppNavigationController`, `TppNoiseSystem`, `TppNoticeSensor` |
| `0x142022000 - 0x142033000` | Player2 (Snake Actions) | 73 | 24 | `TppPlayer2CameraParameterSystem`, `TppPlayerCarryActionPlugin`, `TppPlayerClimbActionPlugin`, `TppPlayerFultonActionPlugin` |
| `0x142033000 - 0x142034000` | Rat | 22 | 12 | `TppRatDamageAction`, `TppRatEscapeAction`, `TppRouteController` |
| `0x142034000 - 0x142035000` | SecurityCamera2 | 25 | 13 | `TppSecurityCamera2DeadAi`, `TppSecurityCamera2DiscoveryController`, `TppSecurityCamera2LifeController` |
| `0x142035000 - 0x142036000` | SmartAnimal | 26 | 11 | `TppSmartAnimalActionController`, `TppSmartAnimalDamageHandler`, `TppSmartAnimalLifeController` |
| `0x142036000 - 0x142046000` | Soldier2 (Enemy Soldiers) | 165 | 74 | `TppSoldier2CombatSniperAi`, `TppSoldier2CombatTurretAi`, `TppSoldier2DamageAction`, `TppSoldier2ReloadAction` |
| `0x142046000 - 0x142048000` | UI, Vehicles & Systems | 57 | 7 | `TppUILyric`, `TppUIResult`, `TppBalloonSystem`, `TppBulletSystem3`, `TppCasingSystem`, `TppDungSystem`, `TppFobGameDaemon` |
| `0x142048000 - 0x14204c000` | Vehicle2 & WalkerGear2 | 61 | 30 | `TppVehicleRealizer`, `TppWalkerGear2`, `TppWalkerGear2ActionController`, `TppWalkerGear2CommandAi` |
| `0x14204c000 - 0x14204e000` | Wolf & Zebra | 25 | 9 | `TppWolfDamageAi`, `TppWolfDeadAi`, `TppWolfSleepAi`, `TppZebra` |
| `0x14204e000 - 0x142052000` | BossQuiet2 (Boss Quiet Fight) | 88 | 50 | `TppBossQuiet2CollisionController`, `TppBossQuiet2CombatAi`, `TppBossQuiet2Core`, `TppBossQuiet2EffectHandler` |
| `0x142052000 - 0x142054000` | Horse2forVr & VR Systems | 19 | 12 | `TppHorse2forVrDamageHandler`, `TppHorse2forVrFlagInfo`, `TppHorse2forVrLifeController`, `TppHorse2forVrNormalAi` |
| `0x142054000 - 0x142058000` | Cyprus / Liquid2 (Prologue) | 32 | 24 | `TppLiquid2Core`, `TppLiquid2CoreAi`, `TppLiquid2DamageAction`, `TppLiquid2DemoAi` |
| `0x142058000 - 0x14205c000` | Parasite2 (Skulls Unit) | 78 | 55 | `TppParasite2`, `TppParasite2ActionController`, `TppParasite2CoreAi`, `TppParasite2LifeController` |
| `0x14205c000 - 0x142060000` | Sahelan2 (Sahelanthropus) | 72 | 64 | `TppSahelan2Core`, `TppSahelan2CoreAi`, `TppSahelan2DamageAction`, `TppSahelan2JumpAction` |
| `0x142060000 - 0x142061000` | UAV (Drones) | 30 | 22 | `TppUavActionController`, `TppUavActionCore`, `TppUavAiSet` |
| `0x142061000 - 0x142065000` | Volgin2 (Man on Fire) | 67 | 47 | `TppVolgin2`, `TppVolgin2ActionController`, `TppVolgin2DamageAi`, `TppVolgin2forVr` |
| `0x142065000 - 0x142066000` | Ending Systems / Daemons | 13 | 0 | Unresolved (late engine termination daemons) |

---

## 5. Summary of Newly Cracked Class Descriptors

A selection of the newly cracked and verified class descriptor hashes appended to `mgsv_unified_server/data/re/strcode_bruteforced.tsv`:

| Hash (`StrCode64`) | Resolved Class Name | Category / Cluster | Verification Method |
|---|---|---|---|
| `0x3107870b6ab4` | `TppHeli2FlightController` | Heli2 (`0x1420180a0`) | Disassembly of `TppHeli2::SetupSystem` (`0x140DD42F0`) |
| `0xcecdafe571fc` | `TppHeli2CustomizeController` | Heli2 (`0x1420176f0`) | Disassembly of `TppHeli2::SetupSystem` (`0x140DD42F0`) |
| `0xe3e3fce5d6a2` | `TppBalloonSystem` | Global Systems (`0x142046xxx`) | GameObject Type Registry & Hash match |
| `0xff9ce6c0744e` | `TppBulletSystem3` | Global Systems (`0x142046xxx`) | GameObject Type Registry & Hash match |
| `0x4cbd5b8229eb` | `TppCasingSystem` | Global Systems (`0x142046xxx`) | GameObject Type Registry & Hash match |
| `0x21abb3052f13` | `TppDungSystem` | Global Systems (`0x142046xxx`) | GameObject Type Registry & Hash match |
| `0xebe5ed64bc67` | `TppFobGameDaemon` | Global Systems (`0x142046xxx`) | GameObject Type Registry & Hash match |
| `0x15a8f9d04798` | `TppHorse2forVrNormalAi` | Horse2forVr (`0x142052xxx`) | VR Actor AI cluster & Hash match |
| `0x9115e40e6956` | `TppParachuteSystem` | Global Systems (`0x142046xxx`) | GameObject Type Registry & Hash match |
| `0xce9aa06de262` | `TppShellSystem` | Global Systems (`0x142046xxx`) | GameObject Type Registry & Hash match |
| `0xcb41950b7f81` | `TppThrowingSystem` | Global Systems (`0x142046xxx`) | GameObject Type Registry & Hash match |
| `0xea4fe9b141c2` | `TppTitleMenu` | UI Menu (`0x142009xxx`) | Title screen menu callback match |

All additions have been verified via `foxhash.py` StrCode64 computation, committed to `strcode_bruteforced.tsv`, and indexed in `mgsv_knowledge.db` (now containing 174,905 hashes with 0 stale sources).

---

# Milestone 3 Investigation Report: Master GameObject Scheduler, TypeManager Architecture, and Event Message Bus

> **Re-verified 2026-10-21:** clean specs now in [`docs/engine/Scheduler.md`](scheduler.md) and [`docs/engine/Messages.md`](messages.md) (use those). Corrections [x]: GetTypeManager uses `id >> 9` (no mask); Phase 1 is the type-descriptor lifecycle, not pre-physics; `0x140BF3FC0` is a Denuvo thunk, not a plain lookup.

> **Review 2026-10-19:** type registration 0x140BF4620 (84 = 16 + 47 calls) and SendCommand routing [V]; struct layouts not re-checked [I]. Details: `mgsv_unified_server/docs/FOXRE_REVIEW.md`.

**Investigator:** Antigravity (Advanced Static Reverse Engineering Reviewer)  
**Binary Target:** *Metal Gear Solid V: The Phantom Pain* (PC Steam v1.0.15.4 EN, base `0x140000000`, `mgsvtpp.exe`)  
**Knowledge DB Status:** Connected (`mgsv_unified_server/data/knowledge/mgsv_knowledge.db`, 143,899 functions, 9,146 class vtables, 173,985 hashes, 380 SendCommand IDs, 514 command handlers).  

---

## 1. Executive Summary & Core Architectural Spine

Milestone 3 reverse-engineers the runtime execution engine, polymorphic actor scheduling, and event message routing of Konami's Fox Engine. Through static disassembly, persistent headless Ghidra decompilation, and end-to-end call-chain tracing across 11,344 subsystem sites and 385 MessageBus sites, we have established the verified ground-truth specification:

1. **Master `GameObjectManager` Structure & 3-Vtable Multiple Inheritance:**
   - Global singleton allocated at `0x140bf9060` (size `0x470` bytes), stored at `_DAT_142c389a0`, accessed via getter `0x140bf9a10` and type-lookup thunk `0x140bf3fc0`.
   - `GameObjectManager` utilizes MSVC C++ multiple inheritance with **three distinct virtual tables**:
     - **Primary Interface (`+0x00`)**: vtable `0x1423073c0` (9 slots: `0x140bf98d0`..`0x140bf8f20`). Slot 8 is the primary scalar deleting destructor (`FUN_140bf8f20`).
     - **Secondary Interface (`+0x10`)**: vtable `0x142307408` (2 slots: slot 0 `0x140bf9a20` `OnTaskBucketEvent`, slot 1 `0x140bf8ea0` adjusting destructor `-0x10`).
     - **Tertiary Interface (`+0x18`)**: vtable `0x142307418` (2 slots: slot 0 `0x140645940` `re__voidreturn`, slot 1 `0x140bf8eac` adjusting destructor `-0x18`).
   - Internal layout: `+0x00` primary vtable, `+0x08` TaskBucket scheduler channel for `"GameObject"` (`0xc6b72750`), `+0x10` secondary task callback vtable, `+0x18` tertiary interface vtable, `+0x30` array of 128 `TypeSlot` pointers (`0x400` bytes), `+0x430` thread-safe `CreationQueue`, `+0x450`/`+0x451` threading mode flags, and `+0x460` critical section synchronization primitive.

2. **GameObject Type Registration Pipeline:**
   - There are 84 distinct calls across the binary to registration function `0x140bf4620`:
     - `FUN_1405c8b40`: Registers 16 Gimmick/container types (indices 76–91).
     - `FUN_140991bf0`: Registers 47 Core Actor types (indices 0–45, e.g. Player2, Soldier2, Heli2, Sahelan2).
     - Subsystem Initializers: Specialized registrations (e.g. `0x140a23be0` for CommandPost2, `0x140b2e834` for Vehicle2).
   - Real TypeDescriptor vtables:
     - `TppSoldier2TypeDescriptor`: `0x142287c80` (idx=2, hash=`0x3fef1d0298aa`), registered at `0x1409922c0`.
     - `TppHeli2TypeDescriptor`: `0x142288068` (idx=14, hash=`0x89731475623d`), registered at `0x140992597`.
     - `TppSahelan2TypeDescriptor`: `0x142287f50` (idx=21, hash=`0xaa1b15b6a1eb`), registered at `0x140992864`.

3. **Per-Frame Update Phases & Tick Cascade:**
   - Drains `+0x430` creation queue under `+0x460` lock, then loops over all 128 types executing:
     - Phase 1 (`FUN_140bf9620`): Pre-Physics & Lifecycle / Deletion handling.
     - Phase 2 (`FUN_140bf94e0`): Batch Activation & Registration handler for newly spawned instances. Flattens incoming linked list `+0x38` into contiguous vector `+0x20` and invokes `TypeManager::vtable[6]` (`BatchActivateInstances`).
     - Phase 3 (`FUN_140bf91b0`): Post-Physics & Instance compaction, removes dead instances via `TypeManager::vtable[7]` (`DeleteInstances`).

4. **Two-Tier Polymorphic Delegation & SendCommand Routing:**
   - Fox Engine decouples high-level actor dispatch from low-level subsystem handlers:
     - **Tier 1: TypeManager** (`vtable[16]`, offset `+0x80`): Universal polymorphic router (`FUN_1409e9940` for Soldier2, `FUN_140a70c10` for Heli2, `FUN_140a63d60` for Sahelan2).
     - **Tier 2: Gameplay Subsystem Controller**: Inside `vtable[16]`, the TypeManager retrieves the Tier 2 controller via `QueryInterface(StrCode64(TypeName))` and forwards the command:
       - Soldier2: calls `subsystem->vtable[26] (+0xd0)` (`0x141356170`, 131 commands).
       - Heli2: calls `subsystem->vtable[5] (+0x28)` (`0x140dd56f0`, 66 commands).
       - Sahelan2: calls `subsystem->vtable[6] (+0x30)` (`0x1418bb820`, 12 commands).

5. **Full Resolution of Event Delivery Pipeline:**
   - `MessageBus::RaiseMessage` (`MessageBus->vtable[8] (+0x40)`) enqueues events to the `"GameObject"` `TaskBucket`.
   - During frame tick, `TaskBucket::DrainAndDispatchMessages` (`FUN_140180760`) matches subscription filters and invokes bucket callback `puVar5->vtable[0]` (`FUN_140bf9a20` at `GameObjectManager + 0x10`).
   - `FUN_140bf9a20` unpacks `actorId`, locates `TypeManager`, and invokes `TypeManager::vtable[15] (+0x78)`.

---

## 2. Master `GameObjectManager` Structure & 3-Vtable Multiple Inheritance

`GameObjectManager` (`_DAT_142c389a0`, size `0x470` bytes) is allocated in `FUN_140bf9060` via `func_0x000140015fc0(0x470, 8, 0x10001, ...)` and constructed by `FUN_140bf8a20`:

```c
// 0x140bf8a20: GameObjectManager Constructor
undefined8 * FUN_140bf8a20(undefined8 *param_1) {
  *param_1 = &UNK_1423073c0;       // +0x00: Primary Vtable (9 slots)
  param_1[1] = 0;                  // +0x08: pGameObjectTaskBucket
  param_1[2] = &UNK_142307408;     // +0x10: Secondary Vtable (TaskBucket callback interface)
  param_1[3] = &UNK_142307418;     // +0x18: Tertiary Vtable
  param_1[4] = 0;                  // +0x20: Reserved state words
  param_1[5] = 0;
  
  // Initialize 128 TypeSlot pointers (+0x30 .. +0x430)
  for (int i = 0; i < 128; i++) param_1[6 + i] = 0;
  
  // Initialize CreationQueue at +0x430 (size 0x20)
  FUN_140032df0(param_1 + 0x86, 0, 8, 1, 1);
  *(undefined8*)(param_1 + 0x86) = &UNK_1423073a8;
  
  // Acquire "GameObject" TaskBucket (hash 0xc6b72750)
  undefined8 *bucketMgr = (undefined8 *)FUN_140180c00();
  longlong *pBucket = (longlong *)(**(code **)*bucketMgr)(bucketMgr, 0xc6b72750);
  param_1[1] = pBucket;
  
  // Register Secondary Interface (+0x10) as TaskBucket Callback Listener
  (**(code **)(*pBucket + 0x18))(pBucket, param_1 + 2); // TaskBucket::RegisterCallback(this + 0x10)
  re__voidreturn(param_1 + 3);
  return param_1;
}
```

### Complete Specification of All 3 Vtables:

1. **Primary Interface Vtable (`0x1423073c0`, `this + 0x00`, 9 Slots):**
   - **Slot 0 (`+0x00`)**: `0x140bf98d0` — `RegisterTypeSlot(typeIndex, typeHash, allocParam)`: Allocates 72-byte (`0x48`) `TypeSlot` via `FUN_140bf8b30`, stores at `this->typeSlots[typeIndex]`.
   - **Slot 1 (`+0x08`)**: `0x140bf8f60` — `EnqueueTypeDescriptorConfig(config)`: Enqueues configuration to `TypeSlot->pendingQueue` (`+0x10`).
   - **Slot 2 (`+0x10`)**: `0x140bf8f80` — `EnqueueCreationRequest(req)`: Enqueues actor creation into FIFO queue `this + 0x430`.
   - **Slot 3 (`+0x18`)**: `0x140bf90b0` — `ExecuteImmediateTypeTick(config)`: Forces immediate synchronous execution of Phase 1, Phase 2, and compaction for a single type.
   - **Slot 4 (`+0x20`)**: `0x140bf99e0` — `GetTypeManager(actorId)`: Unpacks `typeIndex = (actorId >> 9) & 0x7F`, returns `typeSlots[typeIndex]->pTypeDesc->pConcreteTypeManager`.
   - **Slot 5 (`+0x28`)**: `0x140bf9930` — `GetGameObjectIdByName(outActorId, nameHash)`: Queries `TypeManager::vtable[17] (+0x88)` across all active types.
   - **Slot 6 (`+0x30`)**: `0x140bf9ac0` — `ProcessCreationQueueAndTick()`: Main frame tick. Drains `+0x430` creation queue under lock `+0x460`, then loops over all 128 types executing Phase 1, Phase 2, and Phase 3.
   - **Slot 7 (`+0x38`)**: `0x140bf99c0` — `GetTypeInstanceCount(typeIndex)`: Returns active count `*(uint32_t*)(typeSlots[typeIndex] + 0x40)`.
   - **Slot 8 (`+0x40`)**: `0x140bf8f20` — `ScalarDeletingDestructor(flags)`: Primary destructor. Invokes teardown `FUN_140bf8c10(this)`, frees memory with `func_0x000140015f90(this, 0x10001)` if `flags & 1`.

2. **Secondary Interface Vtable (`0x142307408`, `this + 0x10`, 2 Slots):**
   - **Slot 0 (`+0x00`)**: `0x140bf9a20` — `OnTaskBucketEvent(bucket, pEvent)`: TaskBucket execution callback! Unpacks `actorId` from `pEvent`, locates `TypeManager`, and dispatches via `TypeManager::vtable[15] (+0x78)`.
   - **Slot 1 (`+0x08`)**: `0x140bf8ea0` — `MultipleInheritanceAdjustingDestructor_10(flags)`: Adjusts `this` pointer by `-0x10` back to `GameObjectManager*`, calls common teardown `FUN_140bf8c10`, and deletes if `flags & 1`.

3. **Tertiary Interface Vtable (`0x142307418`, `this + 0x18`, 2 Slots):**
   - **Slot 0 (`+0x00`)**: `0x140645940` — `re__voidreturn()`: Interface sentinel stub.
   - **Slot 1 (`+0x08`)**: `0x140bf8eac` — `MultipleInheritanceAdjustingDestructor_18(flags)`: Adjusts `this` pointer by `-0x18` back to `GameObjectManager*`, calls common teardown `FUN_140bf8c10`, and deletes if `flags & 1`.

---

### 3. Internal `TypeSlot` Structure (Size `0x48`)

Each registered type has a corresponding `TypeSlot` allocated at `+0x30 + (typeIndex * 8)`:
```c
struct TypeSlot {
    void* baseObject;               // +0x00: Initialized by func_0x000141a98cf0
    TypeDescriptor* pTypeDesc;      // +0x08: Pointer to active TypeDescriptor
    std::list<void*> pendingQueue;  // +0x10: Head of pending descriptor configs (+0x18: size)
    std::vector<void*> instances;   // +0x20: Contiguous instance pointer array (+0x28: end, +0x30: cap)
    std::list<void*> activeList;    // +0x38: Active actor linked list (+0x40: activeCount)
};
```

---

### 4. Verified Core TypeDescriptor & TypeManager Map

| Type Index | `id_base` | Type Name | `TypeDescriptor` VT | `StrCode64` Hash | `CreateTypeManager` | `TypeManager` VT | QI Subsystem VT |
|---|---|---|---|---|---|---|---|
| **0** | `0x0000` | `GAME_OBJECT_TYPE_PLAYER2` | `0x142287c08` | `0x47a6b0e918c9` | `0x140a236c0` | `0x1422a5c00` | `0x1423b0980` |
| **1** | `0x0200` | `GAME_OBJECT_TYPE_COMMAND_POST2` | `0x1422ab7a0` | `0x8f0921fb6953` | `0x140a23b10` | `0x1422ab900` | `0x14234d0b0` |
| **2** | `0x0400` | `GAME_OBJECT_TYPE_SOLDIER2` | `0x142287c80` | `0x3fef1d0298aa` | `0x1409e8c70` | `0x14229c4b0` | `0x1423e78f0` |
| **3** | `0x0600` | `GAME_OBJECT_TYPE_HOSTAGE2` | `0x142287ca8` | `0x6f8b205dd5d1` | `0x1409e9e00` | `0x14229c7c0` | `0x14238e810` |
| **14** | `0x1C00` | `GAME_OBJECT_TYPE_HELI2` | `0x142288068` | `0x89731475623d` | `0x140a70360` | `0x1422c54d0` | `0x14234e980` |
| **21** | `0x2A00` | `GAME_OBJECT_TYPE_SAHELAN2` | `0x142287f50` | `0xaa1b15b6a1eb` | `0x140a636b0` | `0x1422c0f40` | `0x14248a150` |
| **50** | `0x6400` | `GAME_OBJECT_TYPE_VEHICLE` | `0x1422edbd0` | `0x968e10b4cb22` | `0x140b2e650` | `0x1422edc50` | `0x1423b2080` |
| **77** | `0x9A00` | `GAME_OBJECT_TYPE_FULTONABLE_CONTAINER` | `0x1421aebd0` | `0xc1a5e14aedd1` | `0x14060a150` | `0x1421bef60` | `0x142371900` |

---

### 5. Two-Tier SendCommand Routing Architecture

When Lua calls `GameObject.SendCommand(target, cmdTable)` (`0x140bfa380`), execution proceeds through two distinct polymorphic tiers:

```
[ Lua Script: GameObject.SendCommand(actorId, { id = "SetAlertRoute", ... }) ]
                                      |
                                      v (0x140bfa380)
   1. Unpack actorId: typeIndex = (actorId >> 9) & 0x7F; instanceIndex = actorId & 0x1FF;
   2. Lookup TypeManager: pTypeMgr = thunk_FUN_147b5c9d0(actorId) -> GameObjectManager::vtable[4];
   3. Compute Command Hash: cmdHash32 = StrCode32(cmdTable.id);
   4. Invoke Tier 1 Virtual Method:
                                      |
                                      v
   +--------------------------------------------------------------------------+
   | TIER 1: TypeManager::vtable[16] (+0x80) (e.g. FUN_1409e9940 for Soldier2)|
   | - Takes (this, luaState, instanceIndex, cmdHash32)                       |
   | - Checks high-level engine command hashes (0x6b9d826, 0xc42ccdDF)        |
   | - Calls Subsystem QueryInterface:                                        |
   |     pSubsystem = pTypeMgr->subsystemQI->vtable3 - 0x0c |
   | - Forwards to Tier 2 Command Jump Table:                                 |
   |     pSubsystem->vtable[26] (+0xd0) (0x141356170)                         |
   +--------------------------------------------------------------------------+
                                      |
                                      v
   +--------------------------------------------------------------------------+
   | TIER 2: Gameplay Subsystem Command Table (0x141356170, 131 commands)     |
   | - Evaluates cmdHash32 in binary search / switch tree                     |
   | - "SetAlertRoute"     -> 0x141357020                                     |
   | - "SetCautionRoute"   -> 0x141357050                                     |
   | - "AddDamage"         -> 0x141357280                                     |
   +--------------------------------------------------------------------------+
```

#### Dispatch Offsets Across Key Types:
- **`TppSoldier2` (Type 2)**: Tier 1 router `0x1409e9940` (`+0x80`) -> Tier 2 Subsystem `+0xd0` (`0x141356170`, 131 commands).
- **`TppHeli2` (Type 14)**: Tier 1 router `0x140a70c10` (`+0x80`) -> Tier 2 Subsystem `+0x28` (`0x140dd56f0`, 66 commands).
- **`TppSahelan2` (Type 21)**: Tier 1 router `0x140a63d60` (`+0x80`) -> Tier 2 Subsystem `+0x30` (`0x1418bb820`, 12 commands).

---

### 6. The Global Event Delivery Pipeline

The delivery path from C++ emission to actor listener execution is completely resolved:

```
[ Gameplay Event Fires in C++ (e.g. FUN_140baa010: VehicleTrouble) ]
                                |
                                v
  1. Package payload: payload[0] = (instance & 0x1ff) | (typeIndex << 9); payload[1] = tag;
  2. QuarkSystemTable = FUN_140bff050(); MessageBus = *(QuarkSystemTable + 0x60);
  3. MessageBus->vtable[8] (+0x40): RaiseMessage(outHandle, 0x6817abdd, payload);
                                |
                                v
  4. TaskBucket::EnqueueMessage("GameObject" TaskBucket @ GameObjectManager + 0x08)
                                |
================================+================================ (Frame Boundary)
                                |
                                v
  5. TaskScheduler ticks: FUN_140180760 (TaskBucket::DrainAndDispatchMessages)
  6. Matches event StrCode64 against registered subscription filters
  7. Invokes Bucket Callback: callback->vtable[0](callback, bucket, &payload)
                                |
                                v
  8. For "GameObject", callback is GameObjectManager + 0x10 (vtable 0x142307408 slot 0)
  9. Executes FUN_140bf9a20:
     - Unpacks actorId: typeIndex = (actorId >> 9) & 0x7F
     - Locates TypeManager: pTypeMgr = this->typeSlots[typeIndex]->pTypeDesc->pConcreteTypeManager
     - Invokes TypeManager::vtable[15] (+0x78): DispatchDirectCommand / HandleBucketMessage!
```

#### Lua `GameObject.SendMessage` FIFO Queue:
In addition to the TaskBucket bus, Fox Engine provides a high-throughput per-type FIFO queue for Lua scripts:

- **Emission (`GameObject.SendMessage`, `FUN_140bfa510`)**: Unpacks actorId, calls `FUN_140bfa840`. Enqueues event into linked list at `0x142c399c8 + typeIndex * 0x18` (pooled via freelist `_DAT_142c389b0`).
- **Drain (`MessageBus::vtable[9]`, `FUN_140bf39c0`)**: Dequeues pending messages for `typeIndex`, popping `actorId` and `messageId` for batch delivery.

---
<small>Source: `docs/ENGINE.md` in the project repository &middot; generated 2026-10-22.</small>
