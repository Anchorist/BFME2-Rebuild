# Where the nightly's files come from

`planner/` is the project's link planner, copied from the tool that builds the hybrid image by hand, at the version
whose SHA-256 values `planner/PROVENANCE.json` lists. It was copied mechanically, with no change to its logic:

1. a fixed list of text replacements: file locations become the `NIGHTLY_*` environment settings that
   `link_play.py` sets, and environment switch names get the `NIGHTLY_` prefix;
2. every comment removed and every docstring replaced by a neutral one;
3. a check that the program text after step 2 parses to exactly the same syntax tree as after step 1.

`planner/PROVENANCE.json` lists, for each file, the SHA-256 of the original and of the copy and the number of step 1
replacements. Step 1 also renames one column header of the size check's report. The modules are:

| File | Role |
| --- | --- |
| `hybrid.py` | the planner: substitutes rebuilt files into the original program's link, bridges names, links |
| `resolve.py` | static symbol resolution over the ordered object list |
| `coffsym.py` | reads COFF objects and archives |
| `localize2.py`, `padobj.py` | patch copies of the original's objects (local names, padded data objects) |
| `libguard.py` | keeps rebuilt library and inline copies from replacing the original's |
| `extents.py` | the size check of every data object in the planned link |

A replay of the copied planner against the hand-built inputs of one development commit reproduced the hand-built plan:
the same 366 files, an identical link response file, and byte-identical patched objects. The size check found no
new and no blocking findings, the same verdict as the hand run.

`play.sh` follows the steps of the hand-run game job: per-run copies of the prefix and the small game files,
private display, registry setup by `regset.py` (copied unchanged), then the test tool. `checks.py` compares
checksum records the same way as the hand-run comparison: frames both records hold, equal count, first differing
frame. The rest of `ci/nightly/` is new.
