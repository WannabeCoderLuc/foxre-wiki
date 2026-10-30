# FRT route sets

Codec `Engine\formats\frt.py` · verifier `Engine\tests\test_frt_roundtrip.py`.
**Gate (2026-10-21): 307 / 307 unique route files round-trip byte-identically** (311 inventory entries); every node's event range lies inside its route's events.
Content [D]: 104,653 routes, 604,395 nodes, 963,624 events, 104 event types (69 named, 72 % of instances; **85 named, 98.7 %** since E6 2026-10-29). Route ids are sorted ascending in every file [D 307/307]; the exe binary-searches them [V].

## Layout (little-endian, version 3 in every file, contiguous, no padding) [D]
```
Header (28 bytes): char[4] "ROUT"; u16 version = 3; u16 routeCount;
                   u32 idsOffset (=28), definitionsOffset, nodesOffset, eventTablesOffset, eventsOffset
Route ids:          routeCount × u32 (StrCode32 of the route name, e.g. "rts_shln_b_1000")
Route definitions:  routeCount × 16: u32 nodesOff, u32 eventTableOff, u32 eventsOff (relative to this record),
                    u16 nodeCount, u16 eventCount
Nodes:              all routes' nodes, 12 bytes each (float x, y, z)
Event tables:       one per node, u16 eventCount, u16 eventStartIndex (into the route's events; first = edge event,
                    the rest = node events)
Events:             48 bytes each
```
(version 2 has 0x14 more header bytes with an origin vector; absent in TPP data.)

## Event (48 bytes)
| Off | Type | Field |
|---|---|---|
| 0x00 | u32 | type (StrCode32, names below) |
| 0x04 | u8 | isNodeEvent (0 edge, 1 node) |
| 0x05 | u8 | aimType: 0 none 857k · 1 static point 100k · 2 character 360 · 3 route-as-sight 3.9k · 4 route-as-object 1.7k [D] |
| 0x06 | u8 | bodySection |
| 0x07 | u8 | isLoop |
| 0x08 | u16 | time |
| 0x0A | i16 | direction |
| 0x0C | 4×u32 | aim params (vector3 / character id / up to 4 route ids, by aimType) |
| 0x1C | 4×u32 | type-specific params (speed, message id, SwitchRoute route+func+arg, SyncRoute table+step, …) |
| 0x2C | 4 bytes | unused padding (was "snippet") [V static + D]: no accessor reads it; 83.8 % zero, the rest are stale exporter bytes (JSON fragments `"pos`, `Name`, `3_cl`, heap-pointer-like words) |

Field semantics per type follow youarebritish's `frt.bt` [W]; the codec keeps events raw.

## Exe reader (E6, 2026-10-29) [V static]
The `frt` resource (extension string 0x142187054, registered by 0x140513430, resource vtable 0x1421874A0) loads the file
in place (0x140513F70 accepts only version 3) and hands AI code a route-data view, vtable **0x142187500**; every AI
user reads events through it with a handle `{vt 0x1422BD7D8, view, u16 route, u16 node, u16 event}` (0x140A50FF0).
All 17 slots read the raw file (route def = ids/defs offsets above; event index = table[node].start + k):

| Slot | VA | Returns |
|---|---|---|
| +0x08 | 0x140514CB0 | node count (def +0x0C) |
| +0x10 | 0x140514D40 | node position, transformed by the route set's world transform (view +0x30..+0x4C) |
| +0x18 | 0x140514CF0 | event count of a node (table u16 +0) |
| +0x20 | 0x140514100 | route index by id: **binary search**, so route ids are stored sorted [V; D all 307 files] |
| +0x28 | 0x140514B50 | type (u32 +0x00) |
| +0x30 | 0x140514010 | isLoop (+0x07 & 1) |
| +0x38 | 0x140514AE0 | type param k (u32 +0x1C + 4k) |
| +0x40 | 0x140514C40 | isNodeEvent (+0x04) |
| +0x48 | 0x140514BC0 | time in seconds = u16 +0x08 × 0.0166833 (1/59.94) |
| +0x50 / +0x58 | 0x1405143E0 / 0x1405149B0 | facing: i16 +0x0A × π/32768 (0x142187588) → rotation, with the set transform |
| +0x60 | 0x140514370 | aimType (+0x05) |
| +0x68 | 0x140514180 | bodySection (+0x06) |
| +0x70 / +0x78 / +0x80 | 0x140514270 / 0x1405141F0 / 0x140514300 | aim as float3 / qword / word k (+0x0C + 4k) |

No slot of this view touches +0x2C..+0x2F. Not checked: code that reads the raw events without going through the view [?].

## Event type names (StrCode32, recovered 2026-10-21, in `strcode_bruteforced.tsv`)
Top: RelaxedIdleAct 135k · RelaxedWalk 107k · RelaxedWalkAct 81k · CautionWalk 66k · Normal 48k · CautionIdleAct 45k · SendMessage 44k · RelaxedStandWalkAct 34k · None 28k · CautionSquatIdleAim 21k · CautionStandIdleAim 15k · CautionStandIdle 14k · VehicleMoveFast 13k · Move 9.8k · VehicleMoveNormal 9.6k … plus Sahelan's StandSearch, StandIdle, PileBunker, BreakSteelTower, SearchMissile, Peep1, JumpWalk, RunOnly, WalkOnly, RunWalk, All (see `docs\SAHELAN.md` §8.3). **2026-10-29 (E6): +16 names** (StrCode32 brute force, `Tools\strcode_brute` with `BRUTE_MASK32=1`; each hit context-checked against its handler / files; now 85 of 104 named, 98.7 % of instances):
edge MoveNormal / MoveSlow / MoveFast / MoveVeryFast (0x6366BEFD / 0xE2647436 / 0x0BAB841A 92k / 0xF5E07DB3 = UAV speed 0 / 1 / 2 / 3 in the UAV route node 0x141955550 [V static]), CautionWalkSearch 0xEC2BF82A 77k, CautionDash 0xF4973B94, JumpOnly 0x8A397464 (s10151, beside RunOnly / WalkOnly);
node WaitIdle 0xAFC35AAB 58k, CautionWalkFire 0x4E92CA60, VehicleIdle 0x75ABAE82, VehicleGetIn 0x0601BD97, HeliIdle 0x4A6C45E5, DisableStealthMode 0xEC9DB415, Snipe 0xA585C417 and SupineSnipe 0xBE536700 (both s10050, Quiet); 0xBF169F98 = StrCode32("") (also the empty aim-route word).

**Still unnamed: 19 types, 12.8k events (1.33 %)**, classified by the exe handler that compares them [V static]:

- vehicle edge (route-start scan 0x14156E580 / 0x14156FA50, with VehicleMove* / VehicleBack*): 0x0274BA40, 0x1D25BD30, 0x4E87F5A9, 0x77FA77E4, 0x9E620826, 0xF1DFFC4E;
- vehicle node (same scan, with VehicleIdle / VehicleFire): 0x3A994F4E, 0xFF8DD83C, 0x9F695B52 (+ handled-but-unused 0x46DCD964, 0x2F00EC35, 0x308987DA);
- soldier node handler 0x141574B90: 0x921226F1 12k, 0x6FC479D7, 0xD7324484, 0x91745EFB, 0xDD3F3F69; 0x141572470: 0x7419BC4C (position check);
- 0x140ED0AC0..0x140ED4D30 group (with CautionRun / CautionWalk): 0x0AF9CFF0, 0x94E22019, 0xA69F808F;
- no immediate in the plain exe: 0xA00447C1 (s10151) [?].

---
<small>Source: `docs/formats/FRT.md` in the project repository &middot; generated 2026-10-30.</small>
