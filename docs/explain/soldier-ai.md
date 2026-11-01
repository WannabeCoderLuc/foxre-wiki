# How soldiers think

*M9, IN PROGRESS: this page describes findings so far and will change. Exact details: Soldier AI. Modding: [Soldiers and alert phases in a mod](../mods/soldier-ai.md). Tags: [V] read in the game's code, [D] measured live, [I] inferred, [?] open.*

## What it is
A base in the game is two layers. Each **soldier** walks, stops and reacts. Above them, a **command post (CP)** holds the base's shared state: its **phase**.

| Phase | Number | In play |
|---|---|---|
| Sneak | 0 | Normal patrols |
| Caution | 1 | Guards are on watch, on different routes |
| Evasion | 2 | The enemy lost you and is searching |
| Alert | 3 | Open fight |

This page covers what is known so far: which soldiers are simulated in full, how they follow routes, and how phases rise and fall.

## Why it matters
This is the point where the engine stops being a file reader and starts behaving like the game. It is also the hardest part to study: the thing under test shoots back, and no two fights are the same.

## How the original does it

### Far mode: most soldiers are barely simulated
The game keeps **18 soldiers realized** (fully simulated) at a time [V, D]. The rest are *unrealized*: they slide along their routes with simple movement.

This is not a distance check, as earlier notes assumed. Each frame the game does the following:

1. Takes soldiers inside the stage window, a 640 x 640 m square around the player, inset by **32 m to enter and 28 m to stay**. The gap stops soldiers flickering at the edge.
2. Scores them by squared distance to the window's centre. Height counts too. Forced soldiers and those already realized in some states get a large bonus.
3. Adds a penalty of 300 m squared for soldiers beyond 70 m that are out of view, when the view test is on.
4. Sorts them and realizes the first 18.

### Walking speeds
Realized soldiers move by animation; unrealized ones use what look like fixed values [D, I].

| Movement | Realized (m/s) | Unrealized (m/s) |
|---|---|---|
| Walk | 0.975 | 0.80 |
| Caution walk | 1.74 | 1.50 |
| Run | 2.50 | 2.00 |
| Caution run | 4.01 | 2.75 |
| Dash | 6.43 | 4.00 |

Where the unrealized values are stored is not decoded [?]. Unrealized soldiers stay on the route's line (99 % within 0.21 m). Realized ones stray a little more (99 % within 1.98 m).

### Following a route
A small step machine runs for each soldier [V]:

- **Leg:** walk to the next node. Starting a leg sends one path request.
- **Node events:** do that node's events in order, such as an idle. `SwitchRoute` and one other event run without stopping.
- **Next node:** wrap round at the end of the route and count a lap. A next node at the same spot skips the walk.

Our model of this order equals the game on **all 1,662 changes in two runs** [D]. An event's `time` field is its wait in frames. Most waits match it closely (median 1.07 times the value), but some last far longer for reasons not yet decoded [?].

### When a soldier sees you
With the player placed 20 m in front of a walking soldier, in two runs [D]:

1. The base goes to alert **6.2 and 6.8 s** later, with shots at once.
2. Soldiers drop out of route following until the fight ends.
3. The base falls back on its own: **alert, then evasion, then caution**, always in that order.
4. **8 other CPs** go to caution about 21 s after this CP enters evasion.
5. At caution the soldier takes a new route.

We have not logged *which* soldier noticed, so one test is unread: with sight distance set to 0, the alert still came, 20 s after the warp against 6 s at scale 100. Something else may have noticed, so this does not show how sight works [?].

### Phase timers: one number, three speeds
*New, read from the code only. Not yet confirmed by reading the value in the running game.*

Each CP has one timer that falls from **1.0 to 0**. It holds no seconds. Each phase has its own rate [V]:

| Phase | Rate per second | Time at that rate |
|---|---|---|
| Caution | 1/2160 | **36 minutes** |
| Evasion | 1/120 | 2 minutes |
| Alert | 1/30 | 30 seconds |

When the timer reaches 0 the CP steps one phase down. The timer stands still at 1.0 for as long as the CP has the player in sight, so alert's 30 seconds only start once you are lost.

The base rates are not the whole story. The rate is multiplied depending on the situation [V]:

- **Alert has a slow band.** Between 0.5 and 0.4, if the player is within 10 m of a certain point or a state flag is set, the rate drops to 10 %, 2.5 % or 1 %. That thin slice then takes 30, 120 or 300 s instead of 3 s.
- Certain player states speed it up, by 2 times or 1.2 times. Another check speeds it up by 1.5 times.
- A neighbouring CP in full alert can pull this CP back into alert when their soldiers are within 70 m of each other.

**What this explains.** Caution lasting so long in our runs fits a 36-minute timer [I]. Alert runs of 58 and 180 s fit the slow band roughly: 27 s + 30 s is close to 58, while 27 s + 120 s leaves about 33 s unaccounted for [I].

**What it does not explain.** Evasion ran 59 and 42 s, or about 26 s when commanded. The table gives 6, 12 or 120 s, so a piece is still missing [?].

## How the new engine does it
- `Engine/world/realize.py` selects realized soldiers from steps 1 and 2 and the budget. **159 of 181 live lists give the same set**, and the rest differ only by the distance a soldier moves in the sample's age, or on the first list after the window moved [D]. The view penalty and slot swaps are not ported.
- `Engine/world/route_follow.py` has the step order and the path request rule.
- **Phase timers are not in the engine yet.** Only the phase order is pinned in tests.

## How we know
Running tests near armed soldiers needs a safety protocol, written after real accidents:

- **Health.** A driver keeps life at maximum: 45 hits under alert, life unchanged.
- **Hands off.** One run was played by hand and had to be thrown away. The driver now stops if the player moves on their own.
- **Soft warps.** A 30 m warp caused fall damage, so warps land 2 m above the terrain.
- **Never save during a run.** One badly timed checkpoint had spawned the player under the map on every boot.
- **Never mix runs.** Free, forced and noticed runs go to separate fixtures, because a forced phase changes what follows it.
- **Other sources of notice.** One run was stopped by a patrol truck that drove past and noticed the player.

Each statement here says how it was checked. Things that differ between two runs, like fight details, are written down as not pinned instead of being averaged.

## Still open
- Log the CP timer live; explain evasion's length [?].
- Log who noticed, then re-read the sight test [?].
- The unrealized speed table and the movement bits 0x30 [?].
- Route steps 4, 5 and 0x10, the same-spot test, and waits longer than their time [?].
- Hearing, combat AI and damage have not been studied here yet. All data is one base, Central Base Camp in Afghanistan.

---
<small>Hand-written article (`docs/site/explain/Soldier-AI.md`) &middot; published 2026-11-01.</small>
