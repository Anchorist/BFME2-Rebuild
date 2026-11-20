# Battle for Middle-earth II: engine rebuild

We are rewriting the program code of *The Lord of the Rings: The Battle for
Middle-earth II* (EA, 2006, patch 1.06) as clean, readable C++ that compiles
back to the exact machine code of the original game.

**Work in progress. Nothing built from this repository can be played yet.**

![Progress](https://raw.githubusercontent.com/Open-BFME/BFME2-Rebuild/progress/progress.svg)

The two numbers that matter:

- **Byte match** ("Code matched" above): how much of the original program's
  code our C++ compiles back to, byte for byte.
- **Linking**: how many of the names a complete game needs our source already
  provides. At 100% the game builds from this source alone.

Nobody types these in. Machines on [Boat](https://boat.dev) measure them
after every change to `main` and again every day around noon US Eastern
time, and a workflow redraws the picture. The full card, with one row
for each part of the game, is on the
[`progress` branch](https://github.com/Open-BFME/BFME2-Rebuild/tree/progress).

## The goal

Source code for the whole game that anyone can read, build and change: fix
bugs, patch it, mod it. The game's source was never released, so it has to be
written again from the shipped program.

To know the new code is right, and not just similar, each function must
compile to the same bytes as the original when built with the 2003 Microsoft
compiler the game was built with.

## How it works

1. You write a function in C++ and open a pull request.
2. The checks compile it with the original compiler and compare the result,
   byte for byte, with the original program in `baseline/game.dat`. They also
   check that the source is ordinary C++ and not assembly in disguise.
3. If it passes, it lands by itself within minutes. If it does not, the
   report names the function or the rule that refused it.

There is nothing to install: the checks run on the project's machines. A pull
request from a fork gets the source rules at once and the compile check after
the maintainer admits it. Changes to shared headers under `include/`, and to
the checks themselves, also wait for the maintainer.

## Where it stands (2026-11-20)

| Question | Answer |
| --- | --- |
| How much code is matched? | About a quarter. The picture above is the live figure. |
| How far is linking? | The daily linking figure is being switched on, so its bar still reads "not measured yet". The last link by hand was missing 3,130 names. |
| Does the rebuilt code behave like the original? | Yes, where it has been tested: 366 rebuilt files (6,147 functions) swapped into the original game play identically on two maps and through save and load. |
| Does the game build from this source alone? | Not yet. Too much is still unwritten for it to link by itself. |

Much of the source is not good yet. Many files are still named by address
instead of by their real name, and many types are stand-ins. An independent
review listed what is wrong: [known weaknesses](docs/known-weaknesses.md).

## Get your agents started

Most of this code is written by AI coding agents, and yours are welcome.

1. Fork the repository and clone your fork.
2. Start your agent in the clone. It reads [AGENTS.md](AGENTS.md) by itself.
3. Give it this to begin:

   ```text
   Read AGENTS.md and docs/agents.md. Pick one small unwritten function from
   worklist/unwritten_with_zero_hour_counterpart.tsv that no open pull request
   claims. Read its bytes in baseline/game.dat and its Zero Hour counterpart
   under reference/. Write it below its FUNCTION line and open a draft pull
   request that starts with a Claim line and the evidence. Then read the
   check's report and fix from it, three rounds at most.
   ```

The [agents guide](docs/agents.md) has the rest: what an agent needs
installed, how to read a function's bytes, how to run several agents without
them colliding, and what gets a pull request refused.

## Take part by hand

1. Pick a file from the [worklist](worklist/README.md).
2. Read the [contribution guide](CONTRIBUTING.md) and look at
   [five finished files](docs/reference-files.md) to see the standard.
3. Open a pull request. The [pull-request guide](ci/README.md) explains what
   the checks report.

A plain clone is enough to start. It holds the original program, to read any
function's bytes from, and the source of Zero Hour (the 2003 predecessor,
which EA released in 2025) under `reference/`, to compare with. On Windows,
clone with long paths enabled:

```sh
git clone -c core.longpaths=true https://github.com/Open-BFME/BFME2-Rebuild.git
```

## More

| Page | What it answers |
| --- | --- |
| [docs/status.md](docs/status.md) | The detailed numbers |
| [docs/measurements.md](docs/measurements.md) | Where each number comes from and what a clone can reproduce |
| [RULES.md](RULES.md) | The source rules a pull request must pass |
| [docs/source-quality.md](docs/source-quality.md) | What good source means here |
| [docs/naming.md](docs/naming.md) | How names are chosen |
| [SECURITY.md](SECURITY.md) | How to report a security problem privately |

The maintainer is the GitHub account [@Ancalgonn](https://github.com/Ancalgonn).

This repository follows the earlier
[Open-BFME-2](https://github.com/Open-BFME/Open-BFME-2) project, which matched
every function byte for byte, one function per file. This one organises that
result into real source files with shared headers
([comparison](docs/status.md#the-earlier-project)).

## Licence and affiliation

This is a modified, derived work. It is not the original program, is not an
Electronic Arts product, and has no affiliation or association with Electronic
Arts Inc. or its affiliates or their employees.

“Command & Conquer” and “Battle for Middle-earth” are named in this repository
only to say which games the code belongs to. This repository is not endorsed by
and does not speak for any owner of those names.

`baseline/game.dat` is the program file of the game, version 1.06, as
Electronic Arts shipped it (its SHA-256 is in `baseline/README.md`). It is in
this repository because everything here is measured against it: the checks
compile each change and compare it with this file, and contributors read the
original bytes of a function from it. It is not covered by this repository's
GPL-3 licence statement, and its presence does not mean any affiliation with,
or endorsement by, Electronic Arts or the owners of the game's names. Apart
from this file the repository holds no executables, game assets or byte
dumps, and contributions may not add any ([CONTRIBUTING.md](CONTRIBUTING.md)).

See [LICENSE](LICENSE) and [NOTICE](NOTICE) for the GPL-3 terms and
third-party notices. The Electronic Arts GPL release and its additional
terms cover the text derived from that release. GameSpy SDK and EA PPMalloc
text retain their own notices and are outside this repository's GPL-3 licence
statement.
