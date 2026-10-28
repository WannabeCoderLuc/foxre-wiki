# Claims ledger

_Created 2026-10-23. Tool `Tools\claims_import.py`, ledger `mgsv_unified_server\data\re\claims.tsv` (+ `claims_summary.json`), verifier `Engine\tests\test_claims_ledger.py`, knowledge DB category `claims`._

Facts that other projects already know (IHHook, Infinite Heaven, V_Framework, the modding wiki) enter as **claims** with provenance. They are not knowledge until one of our own oracles confirms them mechanically ("decode, don't guess"). Only verified claims are promoted into our RE data; contradictions are listed and never applied.

## Sources

| key | what is read | claim kinds |
|---|---|---|
| `ihhook` | `Research\sources\IHHook\IHHook\hooks\`: address table `mgsvtpp_adresses_1_0_15_4_en.h`, prologue patterns `mgsvtpp_patterns.h`, typedefs `mgsvtpp_func_typedefs*.h` | function_address (with pattern + signature) |
| `vframework` | `Community\V_Framework\src`: `AddressSet_day3900.cpp` EN block; `constexpr k…Offset / kOff… = 0x..` in the hook sources (+ the `gAddr.<Name>` functions each file hooks) | function_address, global_address, struct_offset |
| `ih_lua` | installed IH Lua `<game>\mod\**.lua` (not saves / profiles / styles): `NAME = int` table entries, StrCode literals, `id="…"` / `msg="…"`, native API calls and constants, `GOTCHA/NOTE/WORKAROUND` comments | enum_value, hash_name, lua_binding, behaviour |
| `wiki` | `Community\mgsvmoddingwiki.github.io\wiki\*.md`: named `0x14…` addresses (only the 1.0.15.4 row of per-build tables), `NAME = int` lines, StrCode literals / ids / API calls in code, format pages | function_address, global_address, enum_value, hash_name, lua_binding, format_note |

The game folder is read only; nothing is written there.

## Verdicts

Status `V` = mechanically verified, `W` = unverified (evidence column says what was checked), `x` = contradicted by our exe or data.

| kind | `V` when | `x` when |
|---|---|---|
| function_address | function entry (`.pdata` start, leaf, or 16-aligned after int3/ret/nop padding) **with** code references, **and** an identity check: IHHook prologue pattern matches (bytes, or instruction by instruction: IHHook patterns were re-assembled by Ghidra, so `4D 89 C2` stands for `4D 8B D0` = `mov r10, r8`), a second independent source claims the same address (IHHook vs V_Framework, our own `re`/`lua` names), the binding map has a Lua function of that name at that VA, the function sits in a vtable of the named class, uses `StrCode(<name segment>)`, or references a string containing the name | the address is in the middle of an instruction, or the IHHook pattern does not match there |
| global_address | data section, referenced by code, plus identity (second source / vtable of the named class) | address in code or outside the image |
| hash_name | the hash occurs in code (dword/qword immediates `text_imm.db`, `hashuse`, raw 48-bit constant), in fox2 data (`equipIdStrCode32`), or the name is already verified / a vanilla Lua literal | a stated value is not StrCode32/64 of the name |
| enum_value | the binding map (`m4_lua_bindings.json` values, `m4_lua_consts.json`) has the name with that value (or `1 << value` for bit indices, e.g. IH `buttonMasks` vs `PlayerPad`) | the hinted library has the name with another value |
| struct_offset | displacement >= 0x20 accessed (`xrefs.db fields`) inside a function the same V_F file hooks | — |
| lua_binding | `Lib.Func` is registered natively (binding map) | — |
| behaviour, format_note | never (notes point at our spec / tests) | — |

Not `x`: code sites inside a function at an instruction boundary or on an immediate/displacement field (V_F patch points such as `Play_bgm_*` = imm32 of `mov edx, <hash>`) stay `W` with that evidence. Independence: the wiki never corroborates anything (several pages are written from V_F). Struct offsets below 0x20 and hits only in callees stay `W`.

## Promotion

- `[V]` function/global names → `symbol_map.tsv` (source `claims_<src>`, note `claims ledger [V] <id> …`), only for addresses that had no name or only an `inferred` / StrCode-hint row; a replaced row is kept inside the note and restored by the next run. Addresses we already name are never renamed.
- New `[V]` hash names → `strcode_bruteforced.tsv` (used_at `claims:<src> <id> <evidence>`; `(32-bit match)` marks names found only as a StrCode32 immediate).
- Then `python Tools\fast_xrefs.py names`, so `re_decompile` / `re_xrefs` show them.

## Counts (2026-10-23)

<!-- claims:counts:begin -->
| source | kind | V | W | x | total |
|---|---|---:|---:|---:|---:|
| ihhook | function_address | 119 | 63 | 4 | 186 |
| ihhook | global_address | 0 | 1 | 0 | 1 |
| vframework | function_address | 68 | 607 | 0 | 675 |
| vframework | global_address | 0 | 42 | 0 | 42 |
| vframework | struct_offset | 74 | 157 | 0 | 231 |
| ih_lua | behaviour | 0 | 139 | 0 | 139 |
| ih_lua | enum_value | 302 | 291 | 0 | 593 |
| ih_lua | hash_name | 193 | 566 | 0 | 759 |
| ih_lua | lua_binding | 178 | 4 | 0 | 182 |
| wiki | enum_value | 74 | 24 | 0 | 98 |
| wiki | format_note | 0 | 11 | 0 | 11 |
| wiki | function_address | 9 | 5 | 1 | 15 |
| wiki | global_address | 8 | 0 | 0 | 8 |
| wiki | hash_name | 17 | 27 | 0 | 44 |
| wiki | lua_binding | 34 | 0 | 0 | 34 |
| v_sahelan | function_address | 31 | 28 | 0 | 59 |
| v_sahelan | global_address | 0 | 5 | 0 | 5 |
| v_sahelan | hash_name | 2 | 0 | 0 | 2 |
| **all** | | **1109** | **1970** | **5** | **3084** |

Contradictions: 5 (all listed in `claims.tsv`, status `x`; first 25):

| id | source | kind | subject | value | evidence |
|---|---|---|---|---|---|
| C00005 | ihhook | function_address | `BlockMemoryAllocTail` | 0x1400dbb30 | inside function 0x1400dbb20 at +0x10: middle of an instruction ('push r14' at 0x1400dbb2f) |
| C00061 | ihhook | function_address | `io_open` | 0x1418990e0 | inside function 0x141898df0 at +0x2f0: middle of an instruction ('cvtsi2ss xmm3, rax' at 0x1418990de) |
| C00063 | ihhook | function_address | `IsRaining` | 0x1413605f0 | inside function 0x141356170 at +0xa480: middle of an instruction ('call qword ptr [rax + 0x58]' at 0x1413605ef |
| C00182 | ihhook | function_address | `StateRadio` | 0x140d69140 | inside function 0x140d69000 at +0x140: middle of an instruction ('je 0x140d6949b' at 0x140d6913c) |
| C02928 | wiki | function_address | `memcpy` | 0x141a5a0e9 | inside function 0x141a59f70 at +0x179: middle of an instruction ('movzx r11d, word ptr [rbx + 8]' at 0x141a5a0 |

Promotion: symbol_map +25 new names, 0 unnamed/inferred rows replaced, 2 addresses already named differently (kept ours); strcode_bruteforced +0 names.
<!-- claims:counts:end -->

Notes on the numbers: the 4 IHHook contradictions are entries (mostly commented out in IHHook) that point into the middle of an instruction in our build. Most V_F `W` rows are real function entries with callers but no second identity check; they stay queryable in the ledger (`mgsv_query_knowledge(claims, "source:vframework <name>")`) and are not promoted. IH `equipStr32` hashes without a site are equipment names that occur in no exe immediate and in no `equipIdStrCode32` fox2 value.

Ours vs theirs for every contradiction, and the fixes it caused in our data: [`docs\CLAIMS_CONTRADICTIONS.md`](claims-contradictions.md).

## Re-run

```
python Tools\claims_import.py all          # import + verify + promote + report (rewrites the counts above)
python Tools\claims_import.py verify       # ledger only, no promotion
python Tools\claims_import.py promote --dry-run
```

Then `mgsv_update_knowledge_db(mode="sync")` (source `claims`, plus `symbols` / `hashes` after a promotion) and `engine_verify(target="test_claims_ledger.py")`. Needs `GameBackup` exe, `xrefs.db`, `text_imm.db`, `fox2.db` (main workspace; from a worktree set `MGSV_ROOT` / `MGSV_RE_DATA` to the main checkout). Run time ~1 min.

Query: `mgsv_query_knowledge(category="claims", query="status:x")`, `"kind:struct_offset source:vframework"`, a hex VA, or any name; empty query = counts.

---
<small>Source: `docs/CLAIMS.md` in the project repository &middot; generated 2026-10-28.</small>
