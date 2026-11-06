# How soldiers think

*M9, PASS (2026-11-04): the milestone gate passed; open points below may still change details. Exact details: [Soldier AI](../engine/soldier-ai.md). Modding: [Soldiers and alert phases in a mod](../mods/soldier-ai.md). Tags: [V] read in the game's code, [D] measured live, [I] inferred, [?] open.*

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
Realized soldiers move by animation. Unrealized ones use fixed values picked by phase and speed class [V, D].

| Movement | Realized (m/s) | Unrealized (m/s) |
|---|---|---|
| Walk | 0.975 | 0.80 |
| Caution walk | 1.74 | 1.50 |
| Run | 2.50 | 2.00 |
| Caution run | 4.01 | 2.75 |
| Dash | 6.43 | 4.00 |

The unrealized values are not a table: one function holds them as separate constants and picks one by phase (sneak or caution), speed class (walk, run, dash) and a flag; a further factor of 0.772 applies to one kind of move [V]. Every measured unrealized speed is among them. Which bits of a soldier's movement word select which pair is not read live yet [I]. Unrealized soldiers stay on the route's line (99 % within 0.21 m). Realized ones stray a little more (99 % within 1.98 m).

### Following a route
A small step machine runs for each soldier [V]:

- **Leg:** walk to the next node. Starting a leg sends one path request.
- **Node events:** do that node's events in order, such as an idle. `SwitchRoute` and one other event run without stopping.
- **Next node:** wrap round at the end of the route and count a lap. If the soldier already stands within 1 m of the next node, its events start with no walk [V].
- **Arriving:** a walk ends when less than 0.25 m of path is left (1 m for a walker gear) [V]. Two more steps get on and off a truck or walker gear, and one waits at the end of a route until the base hands out a new one [V].

Our model of this order equals the game on **all 1,662 changes in two runs** far from the player, and on **all 945 and 947 changes** with the player standing 30 m from a patrol [D]. An event's `time` field is its wait in frames.

**Why some waits run long.** Most idle events hand the soldier to an "idle acting" action. That action counts the event's time only while the soldier stands idle. Now and then, at a random moment, it plays a short idle animation instead (up to 18 s). The clock stops while the animation plays [V]. So a wait is its time plus the animations played on the way. This held on all 173 such events in two runs [D]. The animation lengths are animation data (M16), so the engine pins the rule, not each wait's exact length.

### When a soldier sees you
With the player placed 20 m in front of a walking soldier, in two runs [D]:

1. The base goes to alert **6.2 and 6.8 s** later, with shots at once.
2. Soldiers drop out of route following until the fight ends.
3. The base falls back on its own: **alert, then evasion, then caution**, always in that order.
4. **8 other CPs** go to caution about 21 s after this CP enters evasion.
5. At caution the soldier takes a new route.

**Who noticed [D, one run].** A log of every notice the game stores shows one soldier only: the walking target saw the player (a sight notice), and the alert came 4.2 s later. The sight-scale test (scale 0 still gave an alert after 20 s) has not been repeated with this log [?].

### Phase timers: one number, three speeds
*Read from the code and confirmed in the running game (two runs, 2026-11-04).*

Each CP has one timer that falls from **1.0 to 0**. It holds no seconds. Each phase has its own rate [V, D: every CP in both runs]:

| Phase | Rate per second | Time at that rate |
|---|---|---|
| Caution | 1/2160 | **36 minutes** |
| Evasion | 1/120 | 2 minutes |
| Alert | 1/30 | 30 seconds |

The timer stands still at 1.0 while the CP has the player in sight, so alert's 30 seconds only start once you are lost. After that it falls by rate x frame time every frame, in 32-bit floats; our engine repeats every drained frame of alert bit for bit [D].

Multipliers exist in the code [V]: alert has a slow band between 0.5 and 0.4, certain player states speed it up, and evasion can drain 10 or 20 times faster. With the player 500 m away **none applied** [D].

### The slow band: the alert lingers where you were seen
The base keeps one **front point** for the whole CP system. While the alert is on and a soldier sees the player (or lost sight less than 1 s ago), the base reads the player's position; if that is **more than 10 m** from the front point, the point jumps there [V]. So the point marks where the fight is, and it only moves when you do.
When the alert timer is between 0.5 and 0.4 and the player is still within 10 m of that point (and within 2 m of its height), the timer falls 100 times slower (x0.01; x0.025 or x0.1 in other CP setups) [V]. That last tenth then takes 300 s instead of 3 s: a base that lost sight of you but knows you are still at the spot does not calm down. Three runs at Wakh Sind Barracks, with sight switched off after the alert so the player stayed unseen at the spot, show the band switching on at timer 0.4995; after the player warps far away the timer falls at the normal rate through the same range [D].

### What really ends a phase: the base's reports
The surprise from the live log: **a timer at 0 does not end a phase.** It only makes the CP start asking. The CP sends numbered requests (radio calls and member reports), and the phase steps down when one of them *finishes* [V, D]:

| Step after you left | Time in both runs |
|---|---|
| Alert timer 1.0 to 0 | 30.0 s |
| First report (0x3C) | about 4 s |
| A wait, then a second report (0x3B); when it ends, the base asks for evasion | about 21 s + 5 s |
| Evasion: reports 0x51, 0x53, then 0x3A ends it, while its timer is still at 0.67 | 61.4 s |
| Caution: timer drains for 36 minutes, then report 0x39 | |

So alert lasted 60.8 s after the player left, in both runs, matching the 58 s of an older run. Older runs that lasted longer (180 s alert, 42 or 59 s evasion) had no request log; report lengths and a re-sighting are the likely causes, not yet shown [?].

### Who does the waiting: investigators and their search point
The "wait" in the table is soldier work, not a clock. The base picks the nearest free soldiers as **investigators** and sends them to one **search point** per base: 3 at the start of alert, 2 more after the first report, 4 when evasion starts. When an investigator finishes searching, it marks the point as done (`CompleteInvestigation`) [V]. In that same frame the base drops every investigator's order and sends the next report (0x3B), which leads to evasion [D, two runs]. Evasion ends the same way, with the investigator's own report 0x3A.

How long is a report? **As long as the soldier's voice line plays** [V]: the base's radio waits for the voice player to go quiet. Measured: 147 frames (2.45 s) for 0x3C and 0x3B, about 11.5 s for 0x51, about 10.4 s for 0x53, 1.6 to 3.0 s for 0x3A depending on who speaks [D].

### A second base
The same chain was captured twice at Wakh Sind Barracks (`afgh_enemyBase_cp`), with a soldier who patrols alone: same order, same investigator counts, same report lengths, same rule for the end of each wait. What differs between runs is how long the investigators take (23 or 31 s in alert, 72 or 119 s in evasion), because they walk and search. At Da Wialo Kallai one run showed a shortcut: an investigator who went indoors sent 0x3B itself before the alert timer ran out, and the base went to evasion at once.

## How the new engine does it
- `Engine/world/realize.py` selects realized soldiers from steps 1 and 2 and the budget. **159 of 181 live lists give the same set**, and the rest differ only by the distance a soldier moves in the sample's age, or on the first list after the window moved [D]. The view penalty and slot swaps are not ported.
- `Engine/world/route_follow.py` has the step order and the path request rule.
- `Engine/world/cp_phase.py` has the rates, the float32 drain and the request order. `test_m9_phase.py` pins them on two runs: drain bit-exact, alert 1798 frames from the last sighting to state 1, each fall-back one frame after its request finishes, evasion 3684 frames in both runs. Request lengths are taken from the log (they are voice line lengths). `role_holds` and `complete_investigation` port the rule that ends an investigation; `test_m9_g5.py` pins the whole chain at the second base. `front_point_update`, `near_point` and `alert_drain_step` port the front point and the slow band; `test_m9_g6.py` checks every logged alert drain update bit for bit.

## How we know
Running tests near armed soldiers needs a safety protocol, written after real accidents:

- **Health.** A driver keeps life at maximum: 45 hits under alert, life unchanged.
- **Hands off.** One run was played by hand and had to be thrown away. The driver now stops if the player moves on their own.
- **Soft warps.** A 30 m warp caused fall damage, so warps land 2 m above the terrain.
- **Never save during a run.** One badly timed checkpoint had spawned the player under the map on every boot.
- **Never mix runs.** Free, forced and noticed runs go to separate fixtures, because a forced phase changes what follows it.
- **Other sources of notice.** One run was stopped by a patrol truck that drove past and noticed the player.
- **Same setup every time.** A save that starts in the helicopter, a night checkpoint, or changed Infinite Heaven options (random route sets) each broke a run in November; the save and options are now fixed for captures.

Each statement here says how it was checked. Things that differ between two runs, like fight details, are written down as not pinned instead of being averaged.

## Still open
- How long an investigator searches before it marks the point done; why evasion's timer runs 40 times slower for most of evasion at the second base [?].
- Why the base kept the player's old position for about 80 frames after a warp; at the village the warp came while the player still counted as seen, which is the likely reason its front point sat at the far spot [I].
- Repeat the sight-scale runs once more each (one run each so far) [?].
- Which movement bits pick the unrealized (phase, speed) pair, read live [I].
- Which idle animation is picked and when (a random draw), and the truck's own arrival test [?].
- Hearing, combat AI and damage have not been studied here yet. Data comes from three Afghan bases (Central Base Camp, Wakh Sind Barracks, Da Wialo Kallai); none from Africa yet.

## For modders
- Phase commands, timers, investigators and a safe test setup: [Soldiers and alert phases in a mod](../mods/soldier-ai.md).
- Routes and path requests: [Navmeshes and routes in a mod](../mods/navigation-and-routes.md).
- Planned extension points (radio types, member roles, search-point completion, phase rates, realize budget): [Soldier AI, "Extension points"](../engine/soldier-ai.md) and [Where things stand for modders](../mods/where-things-stand.md).

---
<small>Hand-written article (`docs/site/explain/Soldier-AI.md`) &middot; published 2026-11-06.</small>
