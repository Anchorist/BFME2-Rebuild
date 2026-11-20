# Nightly build and compare

Every night answers one question: **how much of the rebuilt source can replace the original program while the game
plays exactly as the original does?** It runs in three parts.

1. **Compile** (`.github/workflows/nightly.yml`, every night, 16 parallel jobs on the compiler image
   `boat-small/from=bfme2-compiler-v1`). Every `.c` and `.cpp` file under `src/` at the main commit is compiled with
   the same sealed compiler and judged with the same comparison as a pull request. A file whose functions all match
   the original is a candidate. Each job has a 40-minute deadline and records its machine's CPU count, model, busy
   and hypervisor-taken (steal) time, so a slow night shows whether a machine was slow or starved.
2. **Link, check and play** (a separate private repository, two hours later, one machine that holds the game). The link
   planner starts from the original program's own object files and substitutes every candidate file it can link
   safely. It links that image without forcing unresolved names, checks the size of every data object, and plays
   five fixed games under Wine. Each game records a checksum of the whole game state every 25 frames:
   | Test | What must happen |
   | --- | --- |
   | Udun, seed 1, to frame 1000 | all 40 checksums equal the original's |
   | the same with a deliberate change at frame 500 | the comparison must notice it at frame 500 (negative control) |
   | Fords of Isen II, seed 2, to frame 1000 | all 40 checksums equal |
   | Udun, seed 1, to frame 5000 | all 200 checksums equal |
   | save at frame 600, load, play on | outcome pass, every checksum before the save and after the load equal |

3. **Publish the game result** (`nightly.yml` again, two hours after part 2, only when the repository variable
   `BFME_NIGHTLY_GAME_REPO` names the private repository). Reads the game run's result file from that repository with
   one read-only token and publishes it here, replacing the compile result for the same commit.

Parts 1 and 3 write `nightly.json` and a readable summary to the `nightly` branch. Failures open or update one issue
per kind of failure; a clean night closes it. Run by hand: **Actions → Nightly build and compare → Run workflow** on
`main` (tick `fold_game_result` for part 3).

## Where the result is

- `git show origin/nightly:latest.json` (and `history/<date>-<commit>.json`, `SUMMARY.md`)
- the compile run's summary page and its `nightly-result-a<attempt>` artifact (90 days)
- issues titled `Alarm: Nightly build did not produce a checked image`, `Alarm: Nightly game run crashed or
  stopped early`, `Alarm: Nightly game state differs from the original`, `Alarm: Nightly comparison missed a
  deliberate change`

## `nightly.json` (schema `bfme2-nightly/1`)

| Field | Meaning |
| --- | --- |
| `headline` | one sentence, for example `compiles (3253 of 3253 files compile, 407 match completely); game run not live yet` |
| `sha`, `date`, `run_url` | main commit built, UTC date, the public compile run |
| `result` | `pass` (everything ran and held), `fail`, or `partial` (compiled; the game run is not live or has not run yet) |
| `stages` | `compile` and `link_and_play`: the job results, `runs separately` or `not live` |
| `compile` | files, compiled, compile_errors, fully_matching, shards, slowest/fastest shard seconds, `per_shard` machine facts |
| `provided_required_symbols` | the Linking figure: `[provided, needed]` names (see "Linking" below); `null` when not measured |
| `link_census` | its detail: objects read, needed, missing, provided, missing names by kind, duplicate definitions |
| `files_substituted`, `functions` | rebuilt files and their functions in the linked image |
| `plan`, `link`, `size_check` | planner counts, link result (image, unresolved, duplicates), blocking size findings |
| `starts`, `menu`, `skirmish`, `save_load`, `simulation_equal`, `control_caught` | `true`, `false` or `null` (not run) |
| `equal_frames`, `frames` | checksum frames equal in total; per test first differing frame |
| `tests` | per test: status `pass`, `differs`, `crash` or `control-blind`, frames compared and equal, a sentence |
| `image_sha256`, `image_manifest_sha256` | the linked image and the private image's manifest |
| `timings` | stage seconds, wall minutes and runner minutes per stage |

A `partial` night is not a failure: everything that ran passed, and the game run has not reported. `starts` and
`menu` are both shown by the first game reaching its first recorded frame: the test tool reaches a skirmish only
through the main menu.

## Linking

Linking counts the distinct names (functions and data) that the rebuilt source files refer to, and a name counts as
provided when one of our compiled files, or one of the standard and import libraries the original program also links,
defines it. It is measured in the publish step of every compile run by `link_census.py`, from that run's own objects
and the list of names those libraries define (`link-names/library-names.txt`), resolved the way the linker resolves
them; no game file and no private machine is involved. At 100% every name the rebuilt code needs has a definition,
so the program can be linked from this source alone. The figure rises when a missing function or variable is
written, and the needed count can grow when newly written code refers to more names.

## Why a pull request cannot reach the game

The game's files may not be published, so the machine image that holds them must never serve a job that someone
outside the project can write. A workflow file cannot promise that by itself: anyone can open a pull request that
adds a workflow, and on Boat a job asks for a machine image only by naming it in `runs-on`. Boat looks the name up
among the saved images of the Boat organization that the repository's GitHub account is connected to; it has no
setting that limits an image to one repository, workflow, branch or event. So the protection is where the image
lives, not what our files say:

1. The game image is saved in a **separate Boat organization** that is connected only to a separate **private**
   repository. This repository's connection cannot see it: a job here that names it is refused before any machine
   starts ("a `from=` snapshot that does not exist"). One deliberate probe from this repository shows that refusal.
2. No file in this repository names a machine image that holds game files. The compile image holds the compiler and
   public headers only.
3. The private repository's workflow runs only on its own schedule or by hand, reads this repository's public
   compile results, and writes its result to its own branch. It holds no credential for this repository.
4. This repository reads that result with one token that can only read the private repository, used only by a
   scheduled or hand-started job on `main` (pull requests from forks never receive secrets). Only this repository's
   own workflows write here.
5. What is published passes `ci/nightly/scrub.py` twice (on the game machine and again here): paths are cut to their
   last part and anything the public-text check flags is removed. It never publishes an image, an object, a log or
   a checksum value.

## What stays private

The original program's object files, the game's assets, the Wine prefixes and the original's checksum records live
only on the private image. The compile stage handles only public source and its own objects.

## Files

`compile_main.py` and `plan_shards.py` (part 1), `link_play.py`, `play.sh`, `regset.py`, `checks.py`, `planner/`
(part 2, run by the private repository from this repository's code), `result.py`, `publish_branch.py`, `alarms.py`,
`scrub.py` (all), `fold_in.py` (part 3), `link_census.py` and `link-names/` (Linking). Image layout: [IMAGE.md](IMAGE.md). Origin of the planner files: [PROVENANCE.md](PROVENANCE.md).
Tests: `python3 -B -m unittest discover -s ci/nightly/tests`.
