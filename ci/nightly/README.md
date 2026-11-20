# Nightly build and compare

Every night at 03:17 UTC, `.github/workflows/nightly.yml` answers one question: **how much of the rebuilt
source can replace the original program while the game plays exactly as the original does?**

1. **Compile** (8 parallel jobs on the compiler image `boat-small/from=bfme2-compiler-v1`). Every `.c` and
   `.cpp` file under `src/` at the main commit is compiled with the same sealed compiler and judged with the same
   comparison as a pull request. A file whose functions all match the original is a candidate.
2. **Link, check and play** (one job on a private image that holds the game). The link planner starts from the
   original program's own object files and substitutes every candidate file it can link safely. It then links
   that image without forcing unresolved names, checks the size of every data object, and plays five fixed
   games under Wine. Each game records a checksum of the whole game state every 25 frames:
   | Test | What must happen |
   | --- | --- |
   | Udun, seed 1, to frame 1000 | all 40 checksums equal the original's |
   | the same with a deliberate change at frame 500 | the comparison must notice it at frame 500 (negative control) |
   | Fords of Isen II, seed 2, to frame 1000 | all 40 checksums equal |
   | Udun, seed 1, to frame 5000 | all 200 checksums equal |
   | save at frame 600, load, play on | outcome pass, every checksum before the save and after the load equal |
3. **Publish**: `nightly.json` and a readable summary go to the `nightly` branch, the run's job summary and the
   `nightly-result-a<attempt>` artifact. Failures open or update one issue per kind of failure; a clean night closes it.

Run it by hand: **Actions → Nightly build and compare → Run workflow** on `main`. `skip_game` stops after the
size check. `probe` only checks that the private image starts and holds every input.

## Where the result is

- `git show origin/nightly:latest.json` (and `history/<date>-<commit>.json`, `SUMMARY.md`)
- the run's summary page, and its `nightly-result-a<attempt>` artifact (90 days)
- issues titled `Alarm: Nightly build did not produce a checked image`, `Alarm: Nightly game run crashed or
  stopped early`, `Alarm: Nightly game state differs from the original`, `Alarm: Nightly comparison missed a
  deliberate change`, opened and closed by the workflow

## `nightly.json` (schema `bfme2-nightly/1`)

| Field | Meaning |
| --- | --- |
| `sha`, `date`, `run_url` | main commit built, UTC date, the run |
| `result` | `pass` (everything ran and held), `fail`, or `partial` (the game stage is not live, see below) |
| `stages` | `compile`, `link_and_play`: the job results, or `not live` |
| `compile` | files, compiled, compile_errors, fully_matching, shards, slowest_shard_s |
| `files_substituted`, `functions` | rebuilt files and their functions in the linked image |
| `plan`, `link`, `size_check` | planner counts, link result (image, unresolved, duplicates), blocking size findings |
| `starts`, `menu`, `skirmish`, `save_load`, `simulation_equal`, `control_caught` | `true`, `false` or `null` (not run) |
| `equal_frames`, `frames` | checksum frames equal in total; per test first differing frame |
| `tests` | per test: status `pass`, `differs`, `crash` or `control-blind`, frames compared and equal, a sentence |
| `image_sha256`, `image_manifest_sha256` | the linked image and the private image's manifest |
| `timings` | stage seconds, wall minutes and runner minutes per runner label |

`starts` and `menu` are both shown by the first game reaching its first recorded frame: the test tool reaches a
skirmish only through the main menu.

## What stays private

The original program's object files, the game's assets, the Wine prefixes and the original's checksum records
live only on the private image. That stage uploads only `stage2.json`: counts, verdicts, frame numbers and hashes.
It never uploads an image, an object, a log or a checksum value. The compile stage handles only public source and
its own objects. No job a pull request can start reaches the private image: this workflow runs only on schedule and
by hand on `main`.

## Status

The compile stage needs nothing private and runs on the proven compiler image. The link-and-play stage runs only when
the repository variable `BFME_NIGHTLY_GAME_RUNNER` names the private image's runner label. Until then each night is
`partial` and says so in its summary. Image layout and how to rebuild it: [IMAGE.md](IMAGE.md). Origin of the
planner files: [PROVENANCE.md](PROVENANCE.md). Tests: `python3 -B -m unittest discover -s ci/nightly/tests`.
