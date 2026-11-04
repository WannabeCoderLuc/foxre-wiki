# Messages and commands in a mod

*Based on: [How a frame runs](../explain/frame-loop.md) (M3, PASS) and [The Lua script host](../explain/script-host.md) (M4, PASS). Exact details: [Messages and commands](../engine/messages.md), [Scheduler](../engine/scheduler.md), [Script host](../engine/script-host.md), "Timers and message delivery". Addresses are for 1.0.15.4 EN.*

## The findings
- Lua talks to one game object in two ways: **`GameObject.SendCommand`** runs at once and returns a result; **`GameObject.SendMessage`** queues a value that the object's type reads during its own update [V].
- The engine talks to scripts through a **message bus**. A message has a category (the sender, e.g. `Timer`, `GameObject`, `Block`), a name and up to **four arguments**, each tagged as none, integer or decimal [V].
- The mission script receives them in `OnMessage(subScripts, sender, messageId, arg0, arg1, arg2, arg3)`. `sender` and `messageId` are StrCode32 hashes; an argument with no value arrives as `nil` [V].
- **Returning 1** from `OnMessage` hands the message back: it is delivered again, in the same drain, with its resend count + 1 (`Mission.GetCurrentMessageResendCount()` reads the count) [V].
- The queue holds **128 messages**. A message raised into a full queue is dropped [V].
- Messages raised while the queue is being delivered are delivered in the same pass, after the ones already waiting [V].
- The mission listener subscribes to 24 categories, among them Mission, Block, Demo, GameObject, Marker, Player, Radio, Sound, Timer, Trap, Weather [V].

## How vanilla scripts listen
Vanilla sequence scripts do not usually write `OnMessage` themselves. They declare a `Messages` function that returns a table built with `Tpp.StrCode32Table`, grouped by category, with entries `{ msg = ..., sender = ..., func = ... }` [vanilla Lua]. For example s10070 listens for `ChangePhase` from `sender = "afgh_sovietBase_cp"` with `func = function(arg0, arg1)`, where `arg1` is the phase [vanilla Lua]. The `Tpp` framework turns these tables into the `OnMessage` dispatch. A mod that follows the same pattern reads like vanilla code and gets the hashing done for it.

## Commands: one object, right now
```lua
local id = GameObject.GetGameObjectId("TppSoldier2", "sol_quest_0000")   -- name of the locator
local r  = GameObject.SendCommand(id, { id = "GetPhase", cpName = "afgh_sovietBase_cp" })
```
How the engine handles it [V]:

1. The target is an id (a number) or an identifying table such as `{ type = "TppSoldier2", index = 0 }`.
2. The command name `id = "Name"` becomes StrCode32("Name").
3. The type manager of the object's type (id >> 9) gets the call with the instance number (id & 0x1FF) and the hash.

So a command is a **per-type** switch on a hash. The soldier type alone handles 131 command ids; the knowledge DB of the project lists them per type. A command that the type does not know does nothing useful; check the type before sending.

## Queued values: SendMessage
`GameObject.SendMessage(target, value)` stores `value` as a Lua reference in a per-type FIFO and returns. The type's update pops it later and the previous one is released [V; that the update is the reader is I]. Use it when the receiving system expects it; it is not a general event system.

## Timers
- **Event timers** (`GkEventTimerManager.Start(name, seconds)`, `Stop(name)`, `StopAll()`, `IsTimerActive(name)`): `Start` raises `Timer.Start(name)` at once and `Timer.Finish(name)` when the time is up; `name` arrives as its StrCode32. Starting a running name restarts it; `Stop` cancels with no message [V live]. Vanilla scripts call these 1,114 times.
- **Interval timers** (`Util.SetInterval`, `Util.SetIntervalCached`, `Util.ClearInterval`) run from updater priority 25, the last in the frame [V binding].

## Update order
About 60 times a second the frame runs 18 to 24 updaters, lowest priority first, ties in registration order [V live, two boots]. A few with names [V]: 3 message system, 4 mission script (`OnUpdate`), 7 search and sight checks, 9 damage, 15 notice sensor, 17 music, 25 `Util` intervals. Objects created or removed during a frame take effect at the next frame boundary.

## How this would be used in a mod
*Hypothetical example; not built or tested.* A mod shows a reminder 90 s after a base goes to alert, unless the alert is over by then. It uses one timer and the `OnMessage` arguments.

```lua
-- inside a mission's script table (hypothetical; message names as StrCode32)
local S32 = Fox.StrCode32
local TIMER = "MyMod_AlertReminder"

function this.OnMessage(subScripts, sender, messageId, a0, a1, a2, a3)
  if sender == S32("GameObject") and messageId == S32("ChangePhase") then
    -- check the argument layout of ChangePhase on the reference pages before relying on a0 / a1
    if a1 == TppGameObject.PHASE_ALERT then
      GkEventTimerManager.Start(TIMER, 90)
    else
      GkEventTimerManager.Stop(TIMER)
    end
  elseif sender == S32("Timer") and messageId == S32("Finish") and a0 == S32(TIMER) then
    -- show the reminder here
  end
end
```
Points the example relies on: timer names arrive hashed [V]; `Stop` sends no message [V]; returning nothing (not 1) lets the message go on as usual [V].

## Pitfalls
- **Do not return 1 by accident.** A handler that returns 1 asks for the message again; one that always does can loop inside one drain.
- **128 messages per queue.** A mod that raises many messages in one frame can push the game's own out.
- **`SetPhase` and other state commands are often asynchronous**: they request a change that a later update applies. Wait for the message (`ChangePhase`) instead of reading back at once ([Soldiers and alert phases in a mod](soldier-ai.md)).
- `print` and `Fox.Log` are empty in the release build; log through your own file ([Find and call Lua natives](lua-natives.md)).
- The exact place of the bus drain relative to the mission's `OnUpdate` within a frame is not decoded [?]. Do not depend on it.
- The `GameObject` listener inside the engine (the one that routes bus messages to a type manager) was never called in three traced boots [?]; game object messages that Lua sees come through the mission listener.

## Planned in the new engine
Message ids, command handlers and updaters become registries in M10: a mod can add its own message ids (namespaced StrCode32, collisions refused), listen to any category, chain a command handler and add an updater with its own priority ([Where things stand for modders](where-things-stand.md)).

---
<small>Hand-written article (`docs/site/mods/Messages-And-Commands.md`) &middot; published 2026-11-05.</small>
