# FPK / FPKD packages

Codec `Engine\formats\fpk.py` · verifier `Engine\tests\test_fpk_roundtrip.py` · census `python Tools\fpk_census.py` (→ `Memory\research\fpk_census\census.json`).
**Gate (2026-10-21): 16,354 / 16,354 unique packages round-trip byte-identically** (8,247 fpk + 8,107 fpkd; 18,052 inventory entries), and **732/732** obfuscated `.lua` entries decode to Lua 5.1 source that compiles.
Tags: [V] verified (round trip / decode on every file, exe), [D] holds in every game file, [I], [?].

## Role
Packages are the unit the game streams: `.fpk` holds asset files (models, textures refs, geometry, nav, Lua …), `.fpkd` holds the DataSets that describe them (`.fox2` and aliases). Top 15 entry types [D]: fox2 38,864 · lba 12,495 · fmdl 11,060 · geom 7,982 · vfx 5,034 · grxla 4,621 · htre 4,209 · lpsh 4,130 · obrb 4,096 · uia 4,008 · adm 2,893 · parts 2,756 · uif 2,721 · uilb 2,619 · geoms 2,092 (59 types in all; full list in the census JSON). Packages live inside the QAR archives (`master\chunk*.dat`, `00.dat`, `01.dat`).

## Layout (little-endian)
```
Header (48 bytes)
  0x00 char[6] "foxfpk"
  0x06 u8      kind: 0x00 fpk, 0x64 ('d') fpkd
  0x07 char[3] "win"
  0x0A u32     fileSize (= total length)
  0x0E 18 bytes zero                                  [D]
  0x20 u32     version = 2                            [D]
  0x24 u32     fileCount
  0x28 u32     referenceCount   (0 in 65 %, 1-3 in 35 %, max 10)  [D]
  0x2C u32     0                                      [D]
Entry table (fileCount × 48)
  u32 dataOffset, u32 0, i32 dataSize, u32 0, i32 nameOffset, u32 0, i32 nameLength, u32 0, u8 md5[16]
Reference table (referenceCount × 16)  — paths of other packages this one depends on
  i32 nameOffset, u32 0, i32 nameLength, u32 0
Names: entry names then reference names, each NUL-terminated, back to back; pad to 16
Data: each entry's bytes in table order, each padded to 16
```

- `md5` = MD5 of the stored name bytes. In TPP 1.0.15.4 every name is stored in clear (`/Assets/…`) and matches its MD5 (124,841/124,841) [D]. (The format allows obfuscated names whose MD5 must be looked up in `fpk_dictionary.txt`; the codec keeps the stored MD5 for that case.)
- Layout is canonical in every game file, so `write(read(b)) == b` [V].

## Lua obfuscation [V]
Every `.lua` inside a package (732/732) is XOR-chained: first byte 0x1B or 0x1C (marker), then
`key = little-endian bytes of ~StrCode64(lower-case file name)`; for i in 0..n-2: `key[i % 8] ^= data[i+1]; out[i] = key[i % 8]`; the result ends in a NUL which is dropped. Implemented as `fpk.decode_entry(entry, strcode64)`. `.lba` (121) and `.subp` (16) entries also start with 0x1B/0x1C but are not obfuscated (the decode check fails, data returned unchanged).

## Exe side
- No `foxfpk` byte string exists anywhere in the exe [V]: the loader does not validate the magic (same as FOX2). Parser VA not yet located [?].

## Open
Exe parser VA; meaning of version 2 (constant).

---
<small>Source: `docs/formats/FPK.md` in the project repository &middot; generated 2026-10-30.</small>
