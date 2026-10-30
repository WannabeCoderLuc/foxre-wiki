# Editing fox2 DataSets

*Based on: [Game data](../explain/game-data.md), [Classes, properties and entities](../explain/classes-and-entities.md). Exact details: [FOX2](../formats/fox2.md), [Reflection](../engine/reflection.md), [Entities](../engine/entities.md).*

## The finding
A `.fox2` DataSet is a list of entities: a class plus typed property values [V]. The engine's own registry (exported with `Fox.ExportSerializeInfo()`) lists 1,153 classes and 6,062 properties with type, container and class version [V]. The project's codec reads and re-writes all 44,994 DataSets byte for byte [V]. The loader stops if an entity's class version differs from the engine's [V]. References between entities come in three kinds: EntityPtr (owned, same file), EntityHandle (known, same or other loaded file), EntityLink (named object in another file) [V].

## How it works
- Names inside DataSets are StrCode64 hashes; the string table at the end holds the readable ones.
- Some entities are "loaders" that make the engine act when their DataSet loads: `ScriptBlockData` creates a script-block slot, `TppSimpleMissionData` names the mission script, `StageBlockControllerData` names the common package, `EmblemBlender` sets up the emblem table [V / I].

## How this would be used in a mod
*Hypothetical example.* A mod wants its own script-block slot in free roam instead of borrowing the quest block. It adds one `ScriptBlockData` entity to a DataSet in its mission package, with the properties the registry lists (`name`, `prerequisites`, `sizeInBytes`, `enabled`), writes the file with a byte-exact codec, and diffs it against the original: the diff shows only the new entity and its strings. When the mission loads, the engine gives the entity the first free of the 8 slots, named after it, and `ScriptBlock.GetScriptBlockId("mymod_block")` finds it.

## Pitfalls
- Wrong property types or containers do not fail loudly; check them against the registry.
- Class versions must match the engine's; copy the version from a vanilla entity of the same class.
- Only 8 slots exist; f30010 already uses 4.

---
<small>Hand-written article (`docs/site/mods/Editing-DataSets.md`) &middot; published 2026-10-30.</small>
