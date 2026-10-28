# Checking community addresses

*Based on: [How we verify](../explain/verification.md). Exact details: [Claims ledger](../engine/claims.md), [Contradictions](../engine/claims-contradictions.md).*

## The finding
3,018 facts from IHHook, Infinite Heaven, V_Framework and the modding wiki were imported with their source and checked mechanically against the 1.0.15.4 EN executable and our data: **1,071 verified, 5 contradicted**, the rest not checkable yet [V]. The contradictions: four IHHook address-table entries (three of them commented out in IHHook) and one wiki address point into the middle of other functions [V].

## How it works
A function address counts as verified only if it is a real function start **and** something independent identifies it: IHHook's byte pattern matches, a second source names the same address, the binding map has a Lua function of that name there, it sits in the named class's vtable, or it uses the hash or string of its own name. The wiki never counts as independent (several pages derive from V_Framework).

## How this would be used in a mod
*Hypothetical example.* A plugin author finds `SomeFunction = 0x14...` in a forum post and wants to hook it. Before writing code they look it up in the ledger: if it is [V], the address is a function start and its identity was confirmed; if [W], nothing contradicts it but nothing confirms it either, so they check the prologue bytes themselves; if [x], the address is wrong for this build and hooking it would detour the middle of another function (a crash at best).

## Pitfalls
- Commented-out IHHook entries are hints, not addresses.
- Every check is for 1.0.15.4 EN; a verified address in this build says nothing about another.

---
<small>Hand-written article (`docs/site/mods/Claims.md`) &middot; published 2026-10-28.</small>
