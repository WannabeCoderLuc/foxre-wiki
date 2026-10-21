# Reflection and type database

Engine module `Engine\core\typedb.py` · data `mgsv_unified_server\data\re\fox_edb.json` (game) + `fox2_typedb.json` (data-derived) · verifier `Engine\tests\test_typedb.py` · tools `Tools\edb_import.py`, `Tools\fox2_typedb.py`.
Tags: [V] verified (exe code / live game / all data), [D] all game data, [I], [?].

## Ground truth: the game's own type DB [V]
`Fox.ExportSerializeInfo()` (Lua binding → native 0x140178D50 → exporter **0x1400781A0**) walks the live class registry and writes `tmp/Tpp_edb_win64.xml`. Retail never produces it because `MGS_TPP\tmp\` doesn't exist (and `init.lua`'s boot-time call didn't fire); calling it over the IH pipe with the folder present works (captured 2026-10-21, `Memory\research\typedb_20261021\`).
Contents: platform (win64, little, 64bit, binformat **242** = fox2 magic byte 0xF2, hashver 0), the 25 data types with type ids and strides (ids = FOX2 type ids), and **1,153 classes** (1,137 `entities` + 16 `subentities`) with **6,062 properties** (147 enum-backed).

Per class: name, super, version, category, size, align, block, loadable, creatable, staticProperties.
Per property: name, exportname, storage (always `Instance`), type, ptrtype, offset, container, arraysize, valueformat (always `value`), optional enuminfo {type `switch`|`flags`, name, key/value list}.

Base hierarchy [V]: Entity (48 B) ← Data (120) ← DataSet (296), TransformData (304) ← GameObjectLocator (336); Data ← GameObject (152); Entity ← DataElement (56). (The FoxRe agent's sizes in [`docs\ENGINE.md`](core-architecture.md) were right.)

## Cross-check with the data [V]
Against `fox2_typedb.json` (all 44,994 DataSets, 403 classes, 3,716 class/property pairs, all names resolved):
- 386/403 data classes are in the dump; the 17 missing are `Fx*` VFX node classes (registered outside the exported entity groups) [D].
- classVersion in every DataSet entity == the registry version (0 mismatches).
- 3,372/3,372 static properties seen in data exist in the class chain with identical type and container.
- Serialization order = base class properties first, then derived (as `TypeDB.properties()` returns).
- FOX2 entity header `unknown1` = the class instance size **in the build that wrote the file** (reader checks it only for format < 5), which is why it differs from current sizes [V, [`docs/formats/FOX2.md`](../formats/fox2.md)]. The reader also rejects entities whose classVersion != registry version [V].

## Native registration API (static init per class) [V]
| VA | Role |
|---|---|
| 0x140074C90 | `ClassDescriptor::Init(desc, instanceSize, parent?, flags)`; +0xD0 = instance size, +0xD8 = 0x10 |
| 0x14007D210 | register class name in the global registry (`FUN_14007A4C0()`), sets desc+0x130 bit 2; name String at desc+0xC8 (200) |
| 0x14007D320 | set category string (desc+0xA8) |
| 0x140077940 | add property: StaticArray[1] `(desc, typeId, name, offset)` (2,171 call sites) |
| 0x140077210 / 0x140077850 / 0x140077760 / 0x1400777E0 | add DynamicArray / StringMap / List / StaticArray[n] property |
| 0x140077290, 0x1400772F0, 0x1400773D0, 0x140077360 | EntityPtr (type 13) property, container 0/1/2/3, with pointee class |
| 0x140077620 / 0x140077680 / 0x1400776F0 | FilePtr (type 20) property, container 0/1/2 |
| 0x1400926F0 | PropertyInfo factory: `switch(typeId 0..24)` → 0x48-byte typed PropertyInfo |
| 0x140078020 | Lua accessor registration (`"RW"`/`"rw"` flags) |
Descriptor layout used by the exporter: name +0xC8, parent +0xE0 (IsKindOf walks it, 0x140113480), version u16 +0xDA, category +0xA8, size +0xD0, align +0xD8, flags byte +0x130 (bit 3 = subentity group, bit 4 = block), property map at +0x20/+0x28.
PropertyInfo (0x48 B): vtable (slot 1 = arraySize), name +0x10, offset +0x18, arraysize +0x20, storage/flags +0x24, container +0x28, hidden flag +0x2C bit 0, ptrtype +0x30, enuminfo +0x38.

## Engine API
`TypeDB().classes[name]`, `.chain(name)`, `.is_a(name, base)`, `.properties(name)` (inherited, serialization order), `.property(name, name_or_hash)`, `.resolve(class_hash)`.

## Open
Fx node classes' properties (from data only); dynamic properties (165 entities) — runtime-only, no registry entry.

---
<small>Source: `docs/engine/Reflection.md` in the project repository &middot; generated 2026-10-22.</small>
