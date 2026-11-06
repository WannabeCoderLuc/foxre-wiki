# Navmeshes and routes in a mod

*Based on: [How soldiers find their way](../explain/path-finding.md), [Routes and navmeshes](../explain/routes-and-navmeshes.md). Exact details: [Navigation and routes](../engine/navigation.md), [FRT route sets](../formats/frt.md), [NAV2 navmeshes](../formats/nav2.md). Addresses are for 1.0.15.4 EN. All live numbers come from Afghanistan free roam, sneak phase.*

## The findings
- A route is **authored data**. A soldier's patrol comes from a `.frt` route set, and scripts choose between routes by name [V].
- Each route leg sends **one path request** when it starts [V, D 673 of 673]. Between legs the soldier follows that plan.
- Paths can only be searched **inside loaded map blocks**. Outside them the game plans one straight line, through anything [V, D 93 % of jobs in our capture].
- A node event's `time` is a wait in frames at about 60 per second [V, D].
- Edge events set the move speed class [V].

## Pick the right tool
| You want | Use |
|---|---|
| A guard to patrol elsewhere, using a route that exists | `SetSneakRoute`, `SetCautionRoute` or `SetAlertRoute` |
| To leave the current route now | `SwitchRoute` |
| A new patrol | Add a route to a `.frt` in a package |
| A soldier to go to any point at runtime | Not possible through routes: they must be pre-authored |
| To see why a soldier walks where it does | FoxTrace `navreq` and `soldier` |

## Switching routes from Lua
```lua
local id = GameObject.GetGameObjectId("TppSoldier2", "sol_sovietBase_0003")
GameObject.SendCommand(id, { id = "SetSneakRoute", route = "rts_my_patrol_0000" })   -- used in sneak
GameObject.SendCommand(id, { id = "SetCautionRoute", route = "rts_my_guard_0000" })  -- used in caution
GameObject.SendCommand(id, { id = "SwitchRoute", route = "rts_my_patrol_0000" })     -- now; route = "" releases
```
`SetCautionRoute` does not check the CP's phase [V]. It stores the route to use. Vanilla scripts also pass `point = 0` to `SetSneakRoute` for a start node, and `enabled = false` to `SetCautionRoute` / `SetAlertRoute` to turn the override off.

`IsOnRoute` is true when the route state is 1 or 2. It is false at 0 (starting a route) and 3 (the route action is not running, such as during a fight) [V, I]. `GetUsingRoute` and `GetDoingRouteEventIndex` exist only for helicopters, so they return nil for soldiers [V].

## Writing a route
Read and write `.frt` files with a byte-exact codec, so that a diff shows only your change (`Engine/formats/frt.py` re-encodes all 307 game files identically). Then keep to what the game expects:

**Nodes.** Leave nodes in the order you want them walked. The route wraps round at the end [D].

**Waits.** The event's `time` field is frames: 5 seconds is about 299, the game's own pattern of whole seconds minus one frame. The exe's reader multiplies by 0.0166833, which is 1/59.94 [V]. Expect the wait to be at least about that long; some last far longer, and we don't know why yet [?].

**Speed class.** The edge event sets it [V 0x140ED4C10]:

| Class | Edge events | Realized / unrealized speed |
|---|---|---|
| Walk (default) | `RelaxedWalk`, `RelaxedWalkAct`, `RelaxedStandWalkAct`, `CautionWalk` ... | 0.975 / 0.80 m/s, caution walk 1.74 / 1.50 |
| Run | `RelaxedRun`, `CautionRun`, `CautionRunAim` | 2.50 / 2.00, caution run 4.01 / 2.75 |
| Dash | `CautionDash` | 6.43 / 4.00 |

**Events that do not stop.** `SwitchRoute` runs without a pause, so you can chain routes at a node with no idle [V 0x14156FDC0].

**Two nodes at one spot.** The second one's events run with no walk between them. In our data these were 0 m apart, and real walks began at 1.64 m. The exact limit is not decoded, so keep real legs at 2 m or more [D, ?].

**First leg.** The first leg of a route is requested with a cost multiplier of 2.0 on mask 8 regions, so it may avoid ground a later leg would cross [V]. This can look like an odd detour on a soldier's way to the route.

**On the mesh.** Keep nodes on walkable ground. In a loaded block a start off the mesh gets a straight line, and it does in unloaded blocks too. Goals are snapped to the mesh [V].

## Why soldiers ignore walls far away
Outside the loaded blocks the path is a straight line. This is not a bug to work around:

- Don't time events from a far soldier's arrival. A far soldier's trip differs from a near one in both line and speed.
- Don't judge a route by watching a far soldier on the map. Stand near it.
- Expect positions to jump in line when blocks load and new jobs search properly.

## Paths depend on the moment
Replaying "the same" patrol does not give the same line, because vehicles block triangles under them and active obstacles add rings. A parked truck can change a path. A goal inside an obstacle's box has no goal nodes [V].

## Seeing what happens: FoxTrace
FoxTrace logs without changing game state ([guide](foxtrace.md)):
```text
navreq 20000
soldier 30 6
heartbeat 600
```

| Row | What it gives |
|---|---|
| `navreq` | Each `RequestMove`, with slot and return address |
| `navjob` | Each job: exact input, own output, whether it was a straight line |
| `sol` | All enabled soldiers every 30 frames: position, flags, route, state, node, yaw |
| `rstep` | Each change of route record for one soldier |

Add `navbits` for block bits; it is opt-in as it logs much more. Use `navjob` to pair input with output. `navpath` can show another leg's path.

To read a soldier's route without hooks, the route table is at soldier impl +0xE8: +8 u32 route, +0x10 u16 node, +0x18 u8 event index, +0x20 u8 state [V 0x14157AF10].

## How this would be used in a mod
*Hypothetical example; not built or tested.* A mod makes one guard walk a new loop round a fuel depot, run back when the base is on caution, and leave a message at one stop.

1. **Author the routes offline.** Add `rts_depot_loop` and `rts_depot_return` to the base's `.frt` with a byte-exact tool. The loop has 6 nodes on walkable ground, at least 2 m apart, with `RelaxedWalk` edges. Node 3 gets `RelaxedIdleAct` with `time` = 599 (10 s), then a `SendMessage` event. The return route uses `CautionRun` edges.
2. **Ship the file** in a package the mission loads ([Add a package to a mission](add-a-package.md)).
3. **Assign the routes** when the mission starts:
```lua
local g = GameObject.GetGameObjectId("TppSoldier2", "sol_sovietBase_0003")
GameObject.SendCommand(g, { id = "SetSneakRoute", route = "rts_depot_loop" })
GameObject.SendCommand(g, { id = "SetCautionRoute", route = "rts_depot_return" })
```

4. **Test it standing nearby**, with FoxTrace on. One `rstep` row per change shows whether nodes run in order; `navjob` shows each leg's real path.

## Pitfalls
- Route names are StrCode32 hashes in the file; a typo gives an unknown route and no text error to find.
- Far-mode speed differs from near speed, so a timed meeting between two soldiers can drift depending on where the player stands.
- Far soldiers get 0.80 m/s on every walk event, so walk variants change nothing at a distance.
- The realized budget is only 18 soldiers. See [Soldiers and alert phases in a mod](soldier-ai.md) for forcing a soldier in.
- Our data covers sneak phase in one mission. Check anything else yourself.

---
<small>Hand-written article (`docs/site/mods/Navigation-And-Routes.md`) &middot; published 2026-11-06.</small>
