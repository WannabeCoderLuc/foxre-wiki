# Claims: contradictions

_2026-10-23. Source: `mgsv_unified_server\data\re\claims.tsv` (status `x`), see [`docs\CLAIMS.md`](claims.md). Build 1.0.15.4 EN, static reading of `GameBackup\MGS_TPP\mgsvtpp.exe`._

A claim is contradicted when the address it names cannot be a function entry in our exe: it lands in the middle of an instruction of another function. Tags: [V] read in our exe or data, [I] inferred, [?] open.

| # | Name | Theirs (source) | Ours | Verdict |
|---|---|---|---|---|
| C00005 | `BlockMemoryAllocTail` | 0x1400DBB30 (IHHook address table, commented out) | 0x1400DBB30 is +0x10 inside function **0x1400DBB20** (0x1400DBB20–0x1400DBB66, 2 callers), mid-instruction (`push r14` starts at 0x1400DBB2F) [V] | wrong entry. Their address is exactly +0x10 from a real function start; that function may be the one they meant [?] (no identity check yet) |
| C00061 | `io_open` | 0x1418990E0 (IHHook address table, signature `longlong (lua_State*)`) | 0x1418990E0 is +0x2F0 inside the large function **0x141898DF0**, mid-instruction (`cvtsi2ss` at 0x1418990DE) [V]. Lua's `io.open` is **0x141A30070**: binding map (`io.open`, live) and the static `luaL_Reg` table 0x1424B7270[4] [V] | wrong address. Ours: `io_open` = 0x141A30070 |
| C00063 | `tpp::gm::soldier::impl::anon::IsRaining` | 0x1413605F0 (IHHook, commented out, sig `bool (void* Soldier2, uint)`) | 0x1413605F0 is +0xA480 inside the 5,115-line soldier function **0x141356170** (uses `Area`), mid-instruction (`call [rax+0x58]` at 0x1413605EF) [V] | wrong address; real `IsRaining` not located [?] |
| C00182 | `tpp::gm::impl::cp::ActionControllerImpl::StateRadio` | 0x140D69140 (IHHook, commented out, sig `void (void* ActionControllerImpl, uint, ubyte StateProc)`) | 0x140D69140 is +0x140 inside function **0x140D69000** (0x140D69000–0x140D69215, referenced from 0x142014A70), mid-instruction (`je` at 0x140D6913C) [V] | wrong address; real `StateRadio` not located [?] |
| C02928 | `memcpy` | 0x141A5A0E9 (modding wiki, `Network.md` "Limitations") | 0x141A5A0E9 is +0x179 inside function **0x141A59F70** (vtable 0x1424BDD00 slot 9), mid-instruction (`movzx` at 0x141A5A0E8) [V] | wrong address (odd address, not a function start); CRT `memcpy` not located [?] |

## Consequences in our data (fixed 2026-10-23)
- Four of these names had entered `symbol_map.tsv` earlier from an older IHHook import (`BlockMemoryAllocTail`, `io_open`, `IsRaining`, `StateRadio`), so decompiles showed them at the wrong addresses. Those rows now have no name and carry a `[x] claims Cxxxxx` note.
- 0x141A30070 was named `lua_open` (from the anonymous `luaL_Reg` table); renamed `io_open` [V: binding map `io.open` + table entry `open`].
- Lesson: 3 of the 4 IHHook entries are commented out in IHHook itself (unused, likely from another build); treat commented-out entries as unverified hints.

---
<small>Source: `docs/CLAIMS_CONTRADICTIONS.md` in the project repository &middot; generated 2026-10-30.</small>
