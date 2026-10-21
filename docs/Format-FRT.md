> [!NOTE]
> Generated `from[`docs/formats/FRT.md`](https://github.com/WannabeCoderLuc/mgsvtpp-foxre/blob/main/docs/formats/FRT.md)` on 2026-10-21. Edit the source doc; this page is overwritten on every sync. · [Home](index.md) · [Roadmap](Roadmap.md)

# FRT — route sets (`TppRouteSet`, magic `ROUT`)

Codec `Engine\formats\frt.py` · verifier `Engine\tests\test_frt_roundtrip.py`.
**Gate (2026-10-21): 307 / 307 unique route files round-trip byte-identically** (311 inventory entries); every node's event range lies inside its route's events.
Content [D]: 104,653 routes, 604,395 nodes, 963,624 events, 104 event types (69 named, 72 % of instances).

## Layout (little-endian, version 3 in every file, contiguous, no padding) [D]
```
Header (28 bytes): char[4] "ROUT"; u16 version = 3; u16 routeCount;
 u32 idsOffset (=28), definitionsOffset, nodesOffset, eventTablesOffset, eventsOffset
Route ids: routeCount × u32 (StrCode32 of the route name, e.g. "rts_shln_b_1000")
Route definitions: routeCount × 16: u32 nodesOff, u32 eventTableOff, u32 eventsOff (relative to this record),
 u16 nodeCount, u16 eventCount
Nodes: all routes' nodes, 12 bytes each (float x, y, z)
Event tables: one per node, u16 eventCount, u16 eventStartIndex (into the route's events; first = edge event,
 the rest = node events)
Events: 48 bytes each
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
| 0x2C | 4 bytes | snippet [?] |
Field semantics per type follow youarebritish's `frt.bt` [W]; the codec keeps events raw.

## Event type names (StrCode32, recovered 2026-10-21, in `strcode_bruteforced.tsv`)
Top: RelaxedIdleAct 135k · RelaxedWalk 107k · RelaxedWalkAct 81k · CautionWalk 66k · Normal 48k · CautionIdleAct 45k · SendMessage 44k · RelaxedStandWalkAct 34k · None 28k · CautionSquatIdleAim 21k · CautionStandIdleAim 15k · CautionStandIdle 14k · VehicleMoveFast 13k · Move 9.8k · VehicleMoveNormal 9.6k … plus Sahelan's StandSearch, StandIdle, PileBunker, BreakSteelTower, SearchMissile, Peep1, JumpWalk, RunOnly, WalkOnly, RunWalk, All (`see[docs/SAHELAN.md](https://github.com/WannabeCoderLuc/mgsvtpp-foxre/blob/main/docs/SAHELAN.md)` §8.3). Unnamed: 35 types (0x0BAB841A 92k, 0xEC2BF82A 77k, 0xAFC35AAB 58k, 0x6366BEFD 22k, 0x921226F1 12k, …) [?].
