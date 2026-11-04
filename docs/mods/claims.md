# Checking community addresses

*Based on: [How we verify](../explain/verification.md). Exact details: [Claims ledger](../engine/claims.md), [Contradictions](../engine/claims-contradictions.md). Counts as of 2026-11-04; the ledger page has the current ones.*

## The finding
3,084 facts from IHHook, Infinite Heaven, V_Framework and the modding wiki were imported with their source and checked mechanically against the 1.0.15.4 EN executable and our data: **1,109 verified, 5 contradicted, 1,970 not checkable yet** [V]. The contradictions: four IHHook address-table entries (mostly commented out in IHHook) and one wiki address point into the middle of an instruction of another function [V].

## What the ledger holds
| Kind of claim | Example | Checked by |
|---|---|---|
| function address | an IHHook or V_Framework hook target | is it a real function start, and does something independent identify it? |
| global address | a table or object the community reads | is it referenced by code at all? |
| struct offset | `kOff... = 0x..` in hook sources | is the offset used by the named function? |
| hash name | a name for a StrCode32 / StrCode64 value | does the hash occur in code or data, and does the name hash to it? |

## How a function address is checked
It counts as verified only if it is a real function start **and** something independent identifies it [V]:

- IHHook's byte pattern matches at that address;
- a second source names the same address;
- the binding map has a Lua function of that name there;
- it sits in the named class's vtable;
- or it uses the hash or string of its own name.

The wiki never counts as independent, because several pages derive from V_Framework.

## The five contradictions
| Name | Claimed address | What is really there |
|---|---|---|
| `BlockMemoryAllocTail` (IHHook) | 0x1400DBB30 | 0x10 bytes into function 0x1400DBB20, mid-instruction |
| `io_open` (IHHook) | 0x1418990E0 | 0x2F0 bytes into function 0x141898DF0 |
| `IsRaining` (IHHook) | 0x1413605F0 | inside the soldier command handler 0x141356170 |
| `StateRadio` (IHHook) | 0x140D69140 | 0x140 bytes into function 0x140D69000 |
| `memcpy` (wiki) | 0x141A5A0E9 | 0x179 bytes into function 0x141A59F70 |

Hooking any of these would detour the middle of another function.

## How this would be used in a mod
*Hypothetical example.* A plugin author finds `SomeFunction = 0x14...` in a forum post and wants to hook it. Before writing code they look it up in the ledger:

- **[V]**: the address is a function start and its identity was confirmed. Go ahead, but keep a byte-pattern check in the plugin so it refuses to hook on another build.
- **[W]**: nothing contradicts it, nothing confirms it. Check the prologue bytes yourself, and look for a second, independent identification.
- **[x]**: the address is wrong for this build. Do not hook it.

The same check works for your own finds: an address you found by searching memory is a claim until a second, independent route leads to it.

## Pitfalls
- Commented-out IHHook entries are hints, not addresses.
- Every check is for 1.0.15.4 EN; a verified address in this build says nothing about another.
- [W] is not "probably wrong". Most V_Framework [W] rows are real function starts with callers that lack a second identity check.
- A verified address says what the function **is**, not what its arguments are. Read the reference page for the calling convention before hooking.

---
<small>Hand-written article (`docs/site/mods/Claims.md`) &middot; published 2026-11-05.</small>
