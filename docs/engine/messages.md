# Messages and commands

Re-verification (2026-10-21) of [`docs\ENGINE.md`](core-architecture.md) milestone 3 §5–6. Tags: [V] read in code this pass, [I], [?], [x] corrected.

## GameObject ids [V]
`id = (typeIndex << 9) | instanceIndex` (16 bit; 128 types × 512 instances). `0xFFFF` = none. Type table: `gameobject_type_index.tsv` (e.g. Player2 0, Soldier2 2, Sahelan2 21, Vehicle 50 → ids 0x6400 | i).

## MessageBus (engine → listeners) [V]
- Bus object: `QuarkSystemTable` (`FUN_140BFF050()`) **+0x60**.
- Raise: **bus vt+0x40 `RaiseMessage(bus, &outHandle, messageStrCode32, payload)`**. Example (vehicle code `FUN_140BAA010`): `RaiseMessage(…, StrCode32("VehicleTrouble"), {args[0] = vehicleId (0x6400|i), args[1] = StrCode32("CanNotMove"), args[2..3] = 0, tags = 0x12})`.
- Payload (0x28 B): `u64 args[4]` + `u32 tags` at +0x20 — **3 bits per argument** (arg0 = bits 0–2, arg1 = 3–5, …): 0 none, 1/2 integer, 3 double [V from the listener's decode]. Messages are queued to task buckets and delivered on the bucket tick [I: `FUN_140180760` drain per FoxRe].
- GameObject listener: GOM+0x10 vtable slot 0 `0x140BF9A20`: decodes arg0 as the target id (tag 1/2 → integer, 3 → double), `typeIndex = id >> 9`, then **TypeManager vt+0x78(payload)**.
- These are the messages Lua sees as `Msg` tables (e.g. `GameObject` → `VehicleTrouble`); names are StrCode32 (resolve with `mgsv_query_knowledge(hashes, …)`).

### Live capture (FoxTrace, 2026-10-22) [V live]
- Bus vtable `0x142305E70`; **RaiseMessage = `0x140BF3A30`** (vt+0x40).
- Boot → title → free roam f30010 → ~60 s idle → quit, 2 runs: **43 raises, identical sequence**, all on the frame-job thread:
  - `BuddyAppear` (StrCode32 `0x5ACD262A`) arg0 = `0x2600` (BuddyDog2 #0), tags 2 — at title and again ~110 frames after the f30010 load.
  - `VehicleDisappeared` (`0xB3077E03`) for vehicles `0x6402..0x6414` when the title scene unloads, and `0x6400, 0x6402..0x6414` at quit; caller `0x1416F860F`.
  - `SwitchGimmick` (`0x0E9C20BE`) ×2, args `{0x9E20 (ImportantBreakable #32), 0xAA865930, 0x20F5607B, 1}`, tags `0x492` (four integer args).
- The GameObject listener `0x140BF9A20` was **not called once** in either run → these bus messages are not routed through it; its trigger is still [?].
- Names are 32-bit dictionary matches (one candidate each) [s32]. Fixture: `Engine\tests\fixtures\m3_frame_trace.json`.

## SendCommand (Lua → object, synchronous) [V]
`GameObject.SendCommand(target, {id = "Name", ...})` → `0x140BFA380`:

1. `target` is a number (id) or an identifying table (resolved by `FUN_140BFA290`, e.g. `{type="TppSoldier2", index=0}` → id).
2. TypeManager lookup by id via `0x140BF3FC0` — a **Denuvo thunk** into `.xdata` (behaviour = GOM `GetTypeManager`, slot 4: `typeSlots[id>>9]->desc->typeManager`; not analysed further, project rule).
3. `cmd = StrCode32(table.id)` (`func_1400234F0`); the target arg is removed from the Lua stack.
4. **TypeManager vt+0x80(tm, L, id & 0x1FF, cmd)** returns the Lua result count. The per-type handlers (e.g. Soldier2 `0x141356170` 131 ids, Heli2 `0x140DD56F0`, Sahelan2 `0x1418BB820`) are indexed in the knowledge DB (`mgsv_inspect_handler`).

## SendMessage (Lua → object, queued) [V]
`GameObject.SendMessage(target, value)` → `0x140BFA510` → `FUN_140BFA840(id, luaRef)`:

- `value` is stored as a **Lua registry reference**; node `{next, u16 id, u32 ref}` from a free list at `0x142C389B0` (refilled when empty).
- Appended to a per-type FIFO: head `0x142C399C8 + typeIndex*0x18`, tail `+0x8`; slot `0x142C399C0 + typeIndex*0x18` holds the node being consumed.
- Drain `FUN_140BF39C0(_, typeIndex, &out)`: releases the previously consumed node's Lua ref, pops the next node, returns `{id, ref}`; called by the type's update [I].

## Engine API sketch (M3 implementation)
- `ObjectId` = u16 as above; `MessageBus.raise(name_hash32, args[≤4], tags)`; per-bucket queues drained once per frame; GameObject bucket routes to `TypeManager.on_message(payload)`.
- `send_command(target, table)` → `TypeManager.command(instance, StrCode32(id), lua_args)` (synchronous).
- `send_message(target, value)` → per-type FIFO, consumed by the type's update.

## Open
Bucket manager + `FUN_140180760` drain order (FoxRe [I]); which raises reach Lua `Msg` handlers and when; full Msg name table per sender; when `0x140BF9A20` fires.

---
<small>Source: `docs/engine/Messages.md` in the project repository &middot; generated 2026-10-23.</small>
