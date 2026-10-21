> [!NOTE]
> Generated `from[`docs/formats/QAR.md`](https://github.com/WannabeCoderLuc/mgsvtpp-foxre/blob/main/docs/formats/QAR.md)` on 2026-10-21. Edit the source doc; this page is overwritten on every sync. · [ Home](index.md) · [ Roadmap](Roadmap.md)

# QAR — Fox Engine archives (`master\*.dat`, magic `SQAR`)

Codec `Engine\formats\qar.py` · path hashes `Engine\core\pathcode.py` · verifier `Engine\tests\test_qar_all.py` · census `python Tools\qar_census.py` (→ `Memory\research\qar_census\`), path harvest `python Tools\qar_harvest_paths.py`.
**Gate (2026-10-21), pristine `GameBackup\MGS_TPP\master`: 13 archives, 134,241 entries — every entry decodes with a matching MD5; header, section table and all entry headers re-encode byte-identically; section keys match entry hashes for all entries. Names resolved: 111,394 (83.0 %).**
Tags: [V] verified on every entry, [D] holds in all game data, [I], [?].

## Archives [D]
| Archive | Entries | Compressed | Named |
|---|---|---|---|
| 0\00.dat | 896 | 604 | 875 |
| 0\01.dat | 1,102 | 0 | 462 |
| chunk0–4.dat | 2,885 / 4,375 / 14,115 / 1,948 / 13,722 | 2,284 / 2,698 / 13,580 / 1,584 / 13,128 | 99–100 % |
| data1.dat | 623 | 0 | 621 |
| texture0–4.dat | 33,359 / 8,804 / 21,059 / 14,796 / 16,557 | 0 | 80 / 98 / 76 / 62 / 72 % |
`master\e2f*.dat` (5 files) are ASF videos, not archives. The live Steam install additionally has SnakeBite's `a_chunk7.dat`/`a_texture7.dat` and a modified `00.dat`; always census the `GameBackup` copy.

## Header (32 bytes) [V]
All fields after the magic are XORed with format constants X = (0x41441043, 0x11C22050, 0xD05608C3, 0x532C7319):
| Off | Field | Stored |
|---|---|---|
| 0x00 | magic `SQAR` | plain |
| 0x04 | flags (bit 0x800 → block shift 12, else 10) | ^X0 |
| 0x08 | fileCount | ^X1 |
| 0x0C | unknownCount (16-byte records after the table) | ^X2 |
| 0x10 | blockFileEnd | ^X3 |
| 0x14 | offsetFirstFile | ^X0 |
| 0x18 | version: **1** for every TPP archive | ^X0 |
| 0x1C | unknown | ^X1 |

## Section table [V]
`fileCount × u64` at 0x20; word half j of entry i (byte offset o) is XORed with `X[(i + o/5) % 4]`. Decoded value = `blockIndex << 40 | key40`, with **key40 = (hash & 0xFF) << 32 | hash >> 32** (all 134,241 entries) — the table is a sorted lookup by name hash. Entry header at `blockIndex << blockShift`.

## Entry header (32 bytes) [V]
| Field | Stored |
|---|---|
| hash (u64, PathCode64) | low/high u32 each ^X0 |
| storedSize | ^X1 |
| uncompressedSize | ^X2 (compressed when ≠ storedSize) |
| md5[16] | u32s ^X3, ^X0, ^X0, ^X1 |

## Entry data [V]
1. **Layer 1 (always):** XOR with keystream from an 8-u32 table: 8-byte block i uses pair `2·((hashLow + 8i/11) % 4)` → period 88 bytes. (v2 mixes an MD5 seed; unused in TPP.)
2. **Layer 2 (optional):** if the layer-1 output starts with u32 0xA0F8EFE6 (8-byte header) or 0xE3F8EFE6 (16-byte header), the next u32 is a per-entry key stored right there; the rest is XORed with an LCG stream `b = key | ((key ^ 25974) << 16); b = 278·key + 48828125·b` per u32 (last 0–3 bytes untouched). Used by Lua/JSON in `data1.dat`.
3. **zlib** if compressed.
**MD5** = MD5 of the inflated content for compressed entries, otherwise MD5 of the **layer-1 output including the layer-2 header** [V] (ATOMIZER/GzsTool had the uncompressed case wrong for layer-2 entries).
All constants and the per-entry key are part of the format (key stored next to the data): a codec, not secret-key decryption.

## PathCode64 (entry hash) [V by 111,394 matches]
`hash = extTypeId << 51 | metaFlag << 50 | hash50` — see `Engine\core\pathcode.py`:
- `hash50 = CityHash64WithSeeds(stem, 0x9AE16A3B2F90404F, seed1) & (2^50-1)`, stem = path without extension and without leading `/Assets/`, seed1 = last 8 bytes of stem reversed (LE u64).
- meta flag for paths outside `/Assets/` or under `/Assets/tpptest`.
- extTypeId = `hash50(ext) & 0x1FFF` over GzsTool's extension list (`1.ftexs` … `6.ftexs` are distinct types).
- CityHash body: identical to the one StrCode64 uses (> 64-byte body = the game's, `Engine\core\strcode.py`).

## Names
Sources (in `Tools\qar_census.DICTS`): GzsTool `qar_dictionary.txt`, `mgsv-lookup-strings` qar + `tpp_file_dictionary.txt` (267k) + fmdl texture paths, and 94,068 paths harvested from the game's own packages and DataSets. Unnamed 22,847 entries are mostly `.ftexs`/`.ftex` in texture0/2/3/4 that no dictionary contains — a real name gap [?], not a hashing error.

## Exe side
Not traced yet [?] (loader = FoxFS / `foxfs.dat`, `foxpatch.dat` strings at 0x1420AE6E8).
