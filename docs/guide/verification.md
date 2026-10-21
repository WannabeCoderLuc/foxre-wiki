# How we verify

*Why the specifications on this site can be trusted, and how to tell how sure each statement is.*

## Pass or fail, decided by a computer
Plausible-looking reverse engineering can still be wrong. So every milestone has a **gate**: an automated test that either passes or fails, written before the work counts as done. The tests run with `engine_verify` and currently cover 19 checks across all the game files mentioned on this site.

## Three kinds of evidence
| Kind | How it works | Example |
|---|---|---|
| **Round trip** | read every file of a type and write it back; the bytes must be identical | 44,994 DataSets, 16,354 packages |
| **Emulator oracle** | run one function of the original game in an emulator and compare with our version | the game's string hash, including long strings |
| **Live fixture** | ask the running game, record its answers, and compare with our tools | 17 object names and positions in free roam |

Test files are locked with checksums, so a test can't quietly be changed to make broken code pass.

## Confidence tags
Statements in the reference pages carry a tag:
| Tag | Meaning |
|---|---|
| **[V]** verified | seen in the program's code or confirmed in the running game |
| **[D]** data | holds for every relevant file in the game data |
| **[I]** inferred | the most likely explanation, not yet proven |
| **[?]** unknown | open question |
| **[x]** corrected | an earlier claim that turned out wrong |

## Boundaries
- The game executable is never modified; all live checks use the game's own Lua interface or small logging plugins in single-player, offline.
- Code protected by Denuvo is not analysed; when a trace reaches it, the investigation stops there.
- No game files, extracted data or decompiled code are published.

---
<small>Source: `docs/guide/Verification.md` in the project repository &middot; generated 2026-10-22.</small>
