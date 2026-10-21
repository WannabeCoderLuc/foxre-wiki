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

## Per-frame update job (`0x140BF5350`) [V]
Runs once per frame (no static caller: registered at runtime):
1. `GOM->Tick()` (above).
2. Merge newly registered updaters (+0xB0 list) into the sorted array +0x98 (sort `FUN_140BF4C10`: ascending `updater->vt[0]()` = priority).
3. Call every updater's **vt+8 Update** in that order.
Updater registration `FUN_140BF4B00(service, typeDescriptor)`: allocates a 0x38-B entry (vtable `0x1423063F8`, ctor `FUN_140BF4690`) wrapping `desc->typeManager`; the TypeManager fills the entry's config via **vt+0x40** (u16 group at +0x08, counts at +0x0C/+0x10/+0x14, bitset allocated for +0x0C bits); the entry goes into one of **4 group lists** (0x20 B each at service+0x00..0x80), each kept sorted (`0x140BF4C40`). Shutdown `FUN_140BF5290` calls every updater's vt+0x10.
Service singleton `0x142C38478` (0xD8 B); its ctor `0x140BF4770` is a Denuvo thunk (not analysed).

## Command and message entry points (verify next — [`docs\engine\Messages.md`](messages.md))
- Task-bucket listener `0x140BF9A20` [V]: reads the target id from a variant (`+0x20 & 7`: 1/2 integer, 3 double), `typeIndex = id >> 9` (< 128), calls **TypeManager vt+0x78(message)**.
- SendCommand `0x140BFA380` and MessageBus (`QuarkSystemTable+0x60`) — FoxRe claims, re-check pending.

## Open / M3 gate
- Exact per-frame order across systems (which updater groups run when, priorities of each TypeManager) needs a live capture (log-only hook on `0x140BF5350` / the updater vt+8 calls) — `fox-ground-truth`.

---
<small>Source: `docs/engine/Scheduler.md` in the project repository &middot; generated 2026-10-22.</small>
