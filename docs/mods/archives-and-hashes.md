# Archives, packages and hashes

*Based on: [Game data: from disk to objects](../explain/game-data.md) (M1, PASS). Exact details: [QAR archives](../formats/qar.md), [FPK / FPKD packages](../formats/fpk.md). For people writing file tools or checking what a mod package contains.*

## The findings
- The game's files sit in **13 QAR archives** (`master\*.dat`), 134,241 entries. Every entry carries an MD5, and every entry decodes with a matching MD5 in our codec [V]. `master\e2f*.dat` are videos, not archives [D].
- Archives store **no names**, only a 64-bit **PathCode64** per entry. The entry table is sorted by that hash [V].
- The scrambling of archive entries is part of the format: fixed constants plus a key stored next to the data. It is a codec, not secret-key encryption [V].
- **Packages** (`.fpk` assets, `.fpkd` DataSets) are the unit the game loads. Their layout is canonical: reading and writing gives the same bytes for all 16,354 packages [V].
- Every `.lua` inside a package (732 of 732) is lightly obfuscated with a key from the **file name** [V]. Plain-text `.lua` is accepted by the game too (see [For modders](for-modders.md), "Files and packages").
- A package may list **references** to other packages it depends on (35 % do, at most 10) [D].

## Path hashes
`PathCode64 = extensionType << 51 | flag << 50 | hash50` [V, 111,394 matches]:

- `hash50` = CityHash64 (with seeds) of the path **without its extension and without the leading `/Assets/`**, cut to 50 bits.
- `flag` is set for paths outside `/Assets/` or under `/Assets/tpptest`.
- `extensionType` comes from the extension (13 bits). `1.ftexs` to `6.ftexs` are separate types.

Practical consequences:

- Two files with the same path but different extensions have different hashes, but share the low 50 bits.
- To find a file, hash its path; you do not need the archive's name table, because there is none.
- A path you invent for your mod gets a hash like any other. Pick one under your own folder (for example `/Assets/mymod/...`) so it cannot collide with the game's names by accident.

## Names you can trust
The project's name list resolves **83 %** of archive entries (from GzsTool, mgsv-lookup-strings and 94,068 paths harvested from the game's own packages and DataSets) [D]. The unnamed 22,847 entries are mostly textures in the texture archives; no dictionary contains their names [?]. Africa's terrain files are among them, which is why [Ground height at any point](ground-height.md) covers Afghanistan and the Cyprus prologue only.

## Package contents
The 15 most common entry types, over all packages [D]: fox2 38,864, lba 12,495, fmdl 11,060, geom 7,982, vfx 5,034, grxla 4,621, htre 4,209, lpsh 4,130, obrb 4,096, uia 4,008, adm 2,893, parts 2,756, uif 2,721, uilb 2,619, geoms 2,092. 59 types in all. Every entry name in a package is stored in clear (`/Assets/...`) together with its MD5 [D].

## How this would be used in a mod
*Hypothetical example; not built or tested.* A modder writes a small check that runs before packing a mod. It catches the mistakes that are hard to see in game:

```python
# hypothetical pre-pack check (Python), using any FPK reader that follows the spec
for entry in package.entries:
    assert entry.name.startswith("/Assets/mymod/"), entry.name        # own folder only
    assert md5(entry.name.encode()) == entry.name_md5                  # name table consistent
    if entry.name.endswith(".lua"):
        compile_lua51(entry.data)                                      # plain text or decoded
assert write(read(original_bytes)) == original_bytes                  # the tool itself is byte-exact
```
The last line is the project's own rule for any codec: if read-then-write changes a vanilla file, the tool is wrong, not the file.

## Pitfalls
- **Use a pristine copy** for any census. The live Steam folder of a modded game has installer archives (`a_chunk7.dat`, `a_texture7.dat`) and a modified `00.dat`.
- `.lba` and `.subp` entries start with the same marker bytes as obfuscated Lua but are not obfuscated [V]. Do not "decode" them.
- For uncompressed entries that carry the second scrambling layer, the MD5 covers the layer-1 output **including** the layer-2 header. Some older tools got this case wrong [V].
- The executable never checks the `foxfpk` magic [V: the string does not exist in it]. A broken package may load further than you expect and fail later.

---
<small>Hand-written article (`docs/site/mods/Archives-And-Hashes.md`) &middot; published 2026-11-06.</small>
