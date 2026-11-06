# Addresses, hashes and tags

*Hand-written. How the site writes addresses, offsets, hashes, ids, units and confidence, so a reference page can be read without guessing.*

## Build
Every address and offset on this site is for **MGSV:TPP PC Steam 1.0.15.4, English** (`mgsvtpp.exe`). Other builds and languages differ. Before hooking anything from this site, check the address against your own executable (a byte pattern, or the [claims ledger](../mods/claims.md)).

## Addresses and offsets
| Written as | Means |
|---|---|
| `0x141570FA0` | a virtual address in the executable as laid out on disk (preferred base `0x140000000`). A hook finds the live address from the module base at run time. |
| `0x142C62A30` (in a data section) | a global table or object, same notation |
| `impl +0xE8` | a field at byte offset 0xE8 inside an object (here a soldier's implementation object) |
| `vt+0x40` | the function in the object's vtable at byte offset 0x40 (slot 8 on 64-bit) |
| `*(self + 0x70)` | follow the pointer stored at offset 0x70 |
| `stride 0x60` | an array of 0x60-byte records; record i starts at base + i × 0x60 |
| `[dev] Name` | a name taken from a development-build symbol map; treated as [I] until the retail code is read |

Offsets come from reading the code that uses them. A field not used in the code we read may still exist; a layout on a reference page lists only what was seen.

## Hashes
The game rarely stores names as text. Three hashes cover almost everything [V: each checked against the game's own function in an emulator, or against every archive entry]:

| Hash | Width | Used for |
|---|---|---|
| **StrCode32** | 32 bit | message names, command ids in `SendCommand`, values Lua builds with `StrCode32`, large-block names in stage-block messages |
| **StrCode64** | 64 bit, low 48 bits used in DataSets | class names, property names, strings in `.fox2` files, the Lua decode key of packed `.lua` files |
| **PathCode64** | 64 bit | archive entry keys: the hash of the file path without its extension, plus an extension type and a flag |

A name is "known" when some string hashes to the stored value. The project's name lists cover 83 % of archive entries; the rest are mostly textures whose paths nobody has found ([Archives, packages and hashes](../mods/archives-and-hashes.md)).

## Game object ids
`id = (type << 9) | instance`: 16 bits, 128 types of up to 512 instances; `0xFFFF` means none [V]. Examples: player type 0 (ids from 0x0000), soldier type 2 (from 0x0400), vehicle type 50 (from 0x6400). Lua `GameObject.GetGameObjectId(...)` returns these ids.

## Units
- Positions in metres; y is up. Map blocks are 128 m squares ([Locators and map blocks in a mod](../mods/locators-and-blocks.md)).
- Time on reference pages is in **frames** at 60 per second unless it says seconds (2 s fade = 120 live frames [V]).
- Spatial math in the new engine is 32-bit float, like the game's, so results match bit for bit where tests require it.

## Confidence tags
| Tag | Meaning | Can you build on it? |
|---|---|---|
| **[V]** | verified: read in the program's code, or confirmed in the running game | yes |
| **[D]** | holds for every relevant file in the game data, or measured live (soldier pages) | yes, within what was measured |
| **[I]** | inferred: the most likely explanation, not proven | test it first |
| **[?]** | open question | no |
| **[x]** | an earlier claim found wrong | no; the page says what replaced it |
| **[W]** | (claims ledger) a community claim not yet checked | treat as a hint |

Soldier pages use [D] for "measured in live runs", usually with the number of runs. One run is weaker than two.

## Statuses
**PASS**: the milestone's or module's automated gate passes. **IN PROGRESS**: work has started; pages may change. **PLANNED**: not started.

## Names of things
- Files are written with their game path where it is known (`/Assets/tpp/pack/mbdvc/mb_dvc_top.fpk`).
- Missions by number (f30010 = Afghanistan free roam, f30020 = Africa free roam); locations by code (`afgh`, `mafr`, `cypr`).
- Bases by their CP name (`afgh_sovietBase_cp`); soldiers on soldier pages by their instance number in a given run.
- Engine source paths (`Engine/world/cp_phase.py`) refer to the project's private repository.

---
<small>Hand-written article (`docs/site/start/Conventions.md`) &middot; published 2026-11-06.</small>
