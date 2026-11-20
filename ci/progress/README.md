# Progress card and worklists

The workflow `.github/workflows/progress.yml` writes, for the newest main commit on the `state`
branch, the files below to the branch `progress`. Nobody edits them; the same inputs give the same
bytes (the date shown is the main commit's own date). A README can embed the pictures with
`![Progress](https://github.com/Open-BFME/BFME2-Rebuild/raw/progress/progress.svg)`.

| File on `progress` | What |
| --- | --- |
| `PROGRESS.md` | the card: four bars with one sentence each, the nightly checklist, one bar per part of the game, a table of recent history |
| `progress.svg`, `history.svg` | the four bars; the four figures over time |
| `card.json`, `history.json` | the same figures as data (one history point per main commit measured) |
| `worklist/*.tsv` | the worklists, regenerated for the same main commit |
| `worklist/inputs/` | the exact inputs given to `worklist/generate.py`, so anyone can repeat the run |

## Inputs (and nothing else)

- **S**: the `state` branch commit for main commit **M** (`ci/state/STATE-BRANCH.md`): per function,
  verdict and whether it is proven.
- **L**: the ledger of M, `config/map.json`: `rows` (address, size, role, object) and `objects`
  (object id → source file `tu`).
- **T**: the source tree of M (`src/`, `include/`).
- **N**: the nightly result, `latest.json` on the branch `nightly` (written by `.github/workflows/nightly.yml`); optional.
- **H**: `history.json` from the previous `progress` commit; optional.

## Definitions

An **owned function** is a row of L with `role` = `owned`. Its **file** is `objects[row.object].tu`.
Its **size** is `row.size` (bytes of code in the original program). A function is **matched** when S
gives its address, in its own file, the verdict `MATCH`; **proven** when it is matched and S marks it
proven. (`ci/managed-state/progress_card.card_measure`, `ci/managed-check/progress_delta.states`.)

| Figure | Formula | Input |
| --- | --- | --- |
| Code matched | Σ size of matched owned functions ÷ Σ size of all owned functions | S, L |
| Code proven | Σ size of proven owned functions ÷ Σ size of all owned functions | S, L |
| Linking | names a full link of the game needs that our objects provide ÷ names it needs, as `N.provided_required_symbols` = `[provided, required]` | N |
| Finished functions | count of owned functions that are proven, whose file is under `src/` but not `src/unk/` and whose file name is not address-like (`O`/`G` + 8 hex digits, `rva…`, `FUN_…`), and that are either a global function or a member of a class defined at global scope in exactly one header outside `include/Draft/` reachable by `#include` from that file ÷ count of all owned functions (`finished_index.RealHeaders.ready`) | S, L, T |
| Part of the game | Code matched restricted to owned functions whose file is in that part: `src/Code/GameEngine/Source/<part>` → "GameEngine / <part>", likewise `GameEngineDevice`; other `src/Code/<dir>` → `<dir>`; else the first directory under `src/` (`progress_card.subsystem`) | S, L |
| Draft headers in use | headers under `include/Draft/` named by a literal `#include` in `src/` or `include/` (as written, under `include/`, or relative to the includer) | T |
| Nightly checklist | `N.starts`, `N.menu`, `N.skirmish`, `N.simulation_equal` (for `N.equal_frames` frames), `N.save_load`: true = passed, false = failed, absent or N absent = not run yet. If `N.control_caught` is false the card warns that the comparison cannot be trusted | N |
| History | H plus this point, one per main commit, ordered by commit date, last 2,000 kept | H, S |

**Went down** (alarm "A progress figure went down"): the numerator of code matched, code proven,
linking or finished functions is lower than at the previous main commit in the history.

## Worklists

`worklist/generate.py` (from M) runs with M checked out and these inputs, twice, with different hash
seeds; both outputs must be byte-identical:

- `--verdicts`: S, per file and function, as `generate.py` reads it (`worklist/inputs/verdicts.json`);
- `--ranked`, `--unwritten`: the two dated tables in `worklist/` at M turned back into their input form
  (`worklist/inputs/ranked.tsv`, `unwritten.tsv`). Every row is re-checked against the bodies in M and
  rows that now have a body drop out. The reports themselves are made outside this repository; the
  first line of each table keeps their measurement date and revision.

`draft_headers_in_use.tsv`, `draft_headers_unused.tsv` and `stand_in_types.tsv` depend on T only;
`files.tsv` on T, L and S. To repeat a run by hand: check out M, copy `worklist/inputs/` from the
`progress` branch, and run
`python3 worklist/generate.py --root . --revision M --output OUT --unwritten inputs/unwritten.tsv --ranked inputs/ranked.tsv --verdicts inputs/verdicts.json`;
the six tables equal those on `progress` byte for byte.

## Alarms

`progress-failed` (card not written or not published), `worklist-failed` (generation failed or the two
runs differ), `progress-down` (above). Each issue closes by itself when the next run succeeds.
To test: run the workflow by hand with `drill` ticked; it corrupts one state record, both steps refuse
it, and the first two alarms open; the next ordinary run closes them.
