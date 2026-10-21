# Scheduler

Re-verification (2026-10-21) of [`docs\ENGINE.md`](core-architecture.md) milestone 3 (FoxRe agent) against fresh decompiles. Clean-room spec for M3.
Tags: [V] read in code this pass, [I] inferred, [?] open, [x] FoxRe claim corrected.

## GameObjectManager (GOM) [V]
- Singleton: 0x470 B, allocated by `0x140BF9060`, stored at `0x142C389A0`, getter `0x140BF9A10` (plain `mov rax,[rip+..]`).
- Ctor `0x140BF8A20`: vtables primary `0x1423073C0` (+0x00), task-bucket listener `0x142307408` (+0x10), `0x142307418` (+0x18); obtains the **"GameObject" task bucket** (StrCode32 0xC6B72750) from the bucket manager (`func_140180C00`) into +0x08 and registers `this+0x10` as its listener (bucket vt+0x18).
- Layout: +0x30 `TypeSlot*[128]` (indexed by `typeIndex = gameObjectId >> 9`), +0x430 creation queue (lock-free list `FUN_140033220/500`), +0x450 "use lock" flag, +0x451 flag, +0x460 lock.
- Primary vtable: slot 0 `0x140BF98D0` RegisterTypeSlot(index, desc) (allocs 0x48-B TypeSlot), slot 4 `0x140BF99E0` GetTypeManager(id) = `typeSlots[id>>9]->desc(+0x08)->typeManager(+0x20)` ([x] no `& 0x7F` mask), **slot 6 `0x140BF9AC0` Tick**.
- **Denuvo boundary:** the old doc's "type lookup thunk" `0x140BF3FC0` jumps into `.xdata` (0x147B5C9D0) — protected code, not analysed (project rule).

## TypeSlot (0x48 B) [V]
| Off | Field |
|---|---|
| +0x08 | current TypeDescriptor (desc+0x20 = TypeManager, desc+0x38 = state flags: bit0 delete-requested, bit2 active, bit3, bit5 activating) |
| +0x10 / +0x18 | pending descriptors (list) / count |
| +0x20..+0x30 | `std::vector<GameObject*>` live instances |
| +0x38 / +0x40 | newly created instances (list) / count |

## GOM Tick (`0x140BF9AC0`) [V]
1. Drain the creation queue (+0x430; under +0x460 when +0x450): for each request find its type (`func_140BF4340(req+0x30)`) and append it to that slot's new-instance list (+0x38, count +0x40).
2. For every one of the 128 slots, in index order:
   - **Phase 1 `0x140BF9620` — descriptor lifecycle**: if the current descriptor is active and delete-requested, ask the TypeManager (vt+0xA0 "can unload"), remove all instances (vt+0x38), destroy the descriptor; drop flagged pending descriptors; if no current descriptor, activate the next pending one (set bit5, step `FUN_140BF3CB0` until bit2 clears, then `FUN_140BF4480` + `FUN_140BF5520`). ([x] not "pre-physics")
   - **Phase 2 `0x140BF94E0` — add instances**: append the new-instance list to the vector, publish `tm+0x10 = vector.data`, `tm+0x18 = count`, call **TypeManager vt+0x30(firstNew, newCount)**, clear the list.
   - **Phase 3 `0x140BF91B0` — remove instances**: instances flagged dead (`obj+0x48` bit0) are compacted out of the vector (and pending-new list); the removed set is handed to the TypeManager. 

## Per-frame update job (`0x140BF5350`) [V] + live capture (FoxTrace, 2026-10-22)
Runs once per frame on one thread, **~60 per second** [V live, 2 runs]. No static caller (registered at runtime). `param = service` (singleton `0x142C38478`, 0xD8 B; ctor `0x140BF4770` is a Denuvo thunk, not analysed).

1. `GOM->Tick()` = GOM **vt+0x30** (slot 6, above).
2. If the pending list `svc+0xB0/+0xB8` (`std::vector<Updater*>`, guarded by the lock at `svc+0xC8`; filled by `0x140BF54A0`) is non-empty: append each to the updater vector `svc+0x98/+0xA0`, clear the pending list, then **`std::sort` by priority** (comparator `0x140BF4C10`: `a->vt[0]() < b->vt[0]()`, ascending).
   - The sort is MSVC introsort `0x14015CA00`: ranges of ≤ 32 elements go straight to insertion sort (`0x140081840`), which is **stable** → equal priorities keep registration order [V code + live: ties 7×2 and 18×4 keep their order across re-sorts].
3. Call every updater's **vt+8 Update** (no arguments besides `this`) in vector order.
- Live (boot → title → free roam f30010, idle, 2 identical runs): the vector holds **18, 19 or 24 updaters** (3 distinct sets, priorities 0–25; the 24-entry set is active during mission load). Exact lists: `Engine\tests\fixtures\m3_frame_trace.json`. Updater class names [?] (vtables have no QueryInterface name).

## Type update groups (service `+0x00..+0x80`) [V] — [x] these are not the frame updaters
`FUN_140BF4B00(svc, desc)` (via `0x140BF5520` during type activation, requires `desc+0x28 == 0`): allocates a 0x38-B entry (vtable `0x1423063F8`, ctor `FUN_140BF4690`) for `tm = desc+0x20`:

| Off | Field |
|---|---|
| +0x08 | config filled by **TypeManager vt+0x40**: u16 group (0–3) at +0x08, counts at +0x0C / +0x10 / +0x14 |
| +0x18 | u16 = `tm+0x1C` = sort key (= type index in all live samples) |
| +0x20 / +0x28 / +0x30 | TypeManager / bitset of `+0x0C` bits (all set) / u32 state |

`desc+0x28` points back to the entry. Entry vtable slots are bitset accessors (`0x140BF5250` test bit, `0x140BF56E0` set bit), not an update.
The entry is appended to group list `svc + group*0x20` (`std::vector`) and the list re-sorted by the +0x18 key (`0x140BF4C40`).
Live final groups (f30010): group 0 = 2 types (Vehicle 50, type 88), group 1 = 28 (Player2, CommandPost2, Soldier2, Heli2, EnemyHeli, BuddyDog2, Sahelan2, CritterBird …), group 2 = 9 systems (Equip, Collection, Placed, Fulton, Balloon, SupplyCbox, SupportAttack, Cbox …), group 3 = 8 systems (Pickable, Throwing, Shell, Bullet3, Casing, RangeAttack, Decoy, Dung). Who iterates the groups each frame: [?] (likely one of the frame updaters).
Shutdown `FUN_140BF5290` calls vt+0x10 on each registered object (entries vs. updaters not re-checked) [?].

## Command and message entry points (details: [`docs\engine\Messages.md`](messages.md))
- Task-bucket listener `0x140BF9A20` [V]: reads the target id from a variant (`+0x20 & 7`: 1/2 integer, 3 double), `typeIndex = id >> 9` (< 128), calls **TypeManager vt+0x78(message)**.
- SendCommand `0x140BFA380`, SendMessage `0x140BFA510`, MessageBus raise `0x140BF3A30` — verified, see Messages.md.

## Open
- Updater identities (class names) and which updater walks the 4 type groups.
- Removal path of updaters (`0x140BF5630` / `0x140BF5770` via service wrappers) not yet read.

---
<small>Source: `docs/engine/Scheduler.md` in the project repository &middot; generated 2026-10-22.</small>
