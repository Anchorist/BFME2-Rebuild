# Battle for Middle-earth II engine rebuild

## Status, 2026-11-20

**Work in progress: nothing built from this repository can be played yet.**
This project is rebuilding the program code (the "engine") of *The Lord of
the Rings: The Battle for Middle-earth II* (EA, 2006, patch 1.06) as readable
C++ that, compiled with the 2003 Microsoft compiler the game was built with,
produces the same machine code as the shipped game. About a third of the
functions are done; the rebuilt code does not link into a game by itself
yet. The original program is in `baseline/game.dat`, so the original bytes
of any function can be read from a clone.

**Works today.** Three checks start by themselves on every pull request:
the match check compiles the change with the original compiler and compares
it with `baseline/game.dat`, the source rules check the text, and a third
check covers inline virtual functions. A one-file change gets all three
answers in about four minutes; a change to a widely included header takes
twelve to sixteen. A refused change is told which rule refused it. A pull
request from a branch of this repository that passes lands by itself within
a few minutes. A pull request from a fork gets the source rules at once and
the compile check after the maintainer admits it. Every night a job compiles
every source file and publishes the result.

**Not ready yet.** A change under `include/` waits for the maintainer. The
nightly job does not yet play the game. The rebuilt code does not link into
a game by itself.

**Where it stands.** 15,065 of 41,565 functions (36%)
are credited as compiling to the original bytes, 11,766
(28%) with their references proven. 824 source files with code have their real
names; 337 are still named by address.
The source still has stand-in types where the real type is not known yet:
the source rules count 4,177 `void *`, 4,329 C-style pointer casts, 1,939
casts of a call's result and 160 `reinterpret_cast`, and a pull request may
not add to them. The largest substituted build so far, 323 rebuilt files
with the rest taken from the original, played identically to the original on
2026-11-19. Finished files look like [these five](docs/reference-files.md).
Where each number comes from, and what a clone can reproduce:
[docs/measurements.md](docs/measurements.md).

This project reconstructs the engine as maintainable source organized around the
reference build's translation units and shared headers. A translation unit
is one C or C++ source file together with the headers it includes. The
compiler produces one object file for each unit. The target is the game's
version 1.06 `game.dat`. The source should read like an ordinary engineering
project and compile to the reference code.

## Progress in detail

The maintainers recorded these progress counts at
**2026-11-20 18:05 UTC**, revision `d0411931d7` of their
working repository (the tree of this snapshot's `src/`, `include/`,
`config/` and `expected/` is that revision or a later one).

Terms ([full definitions](docs/ledger-and-checks.md#read-the-verdict)): an
*owned function* is one the ledger assigns to a source file here; *credited
MATCH* means it compiles to the original bytes; *proven* means its references
(calls, data) were checked too; a *VERIFIED* object is a whole source file
whose object code equals the original's; a *placeholder* name is a stand-in
for an unknown real name ([naming](docs/naming.md)).

| Measure | At that snapshot |
| --- | ---: |
| Owned functions credited MATCH | 15,065 / 41,565 |
| Credited functions with proven references | 11,766 |
| Whole objects VERIFIED | 155 / 2,154 |
| Headers outside `include/Draft/` | 1,687 |
| Owned function names classified as real / placeholder | 23,563 / 18,002 |

36% of the owned functions had match credit at that snapshot.

Source files with code: **824 named** and **337 still named by
address** (under `src/unk/`, waiting for evidence of their real name and
place). Another 2,093 files hold only generated
annotations and no code yet (1,854 address-named, 239
named); they are scaffolds, counted apart.

In this snapshot's tree, **9 Draft headers are in use** (included by
some file; these are the ones to retire). Another 2,114 Drafts are
unused generated layout guesses: 2,103 are kept as leads for classes not
written yet and 11 are dead copies of headers that now exist outside
`include/Draft/`. See the [worklist](worklist/README.md).

See [the checker verdicts](docs/ledger-and-checks.md#read-the-verdict) for how
bytes, references, names and object verification are measured.

The game does not yet build from this source alone. A link of the rebuilt
objects of revision `49e1914445e4`, the latest link recorded at that snapshot,
still lacked 1 symbols and had
0 duplicate definitions.

In the project's substitution test of 2026-11-19, an executable used
**323 rebuilt translation units** alongside the remaining engine code from
the reference build. Its recorded simulation checksums agreed with the
reference build's on **40 of 40** compared frames on Udun, **200 of 200** in
the extended Udun run and **40 of 40 on Fords of Isen II**, and its
save-and-reload run passed. A deliberately perturbed control run diverged at
frame 500, so the comparison does detect a difference. A larger image of 356
units from the same plan did not yet produce comparable checksums.

## Help rebuild the source

**Pull requests are checked automatically.** Three checks start by
themselves on every pull request. A pull request from a fork gets the source
rules at once and the compile check after the maintainer admits it with the
`boat-ok` label. The [pull-request guide](ci/README.md) describes the checks
and what their reports say.

**Maintainer.** The maintainer is the GitHub account
[@Ancalgonn](https://github.com/Ancalgonn). Changes under `include/`, and to the
checks, workflows, ledger and baseline (see `.github/CODEOWNERS`), wait for
that account's review; source files under `src/` land by themselves when
every check passes. Report security problems privately as described in
[SECURITY.md](SECURITY.md).

Start with the [worklist](worklist/README.md) and
[contribution guide](CONTRIBUTING.md). Good first contributions are a small
group of related functions, replacing a Draft header that is in use with a
real one, or evidence for a name or file assignment. A plain clone is
enough to choose an item, read the original bytes of any function in
`baseline/game.dat`, compare them with the public source of Zero Hour (the
2003 predecessor game, whose source EA released in 2025) and request
evidence. A local check is optional and heavy: it needs Visual Studio .NET
2003, Wine, Python, an LLVM 18 build of the demangler and support files from
the earlier repository at a pinned commit ([tools/README.md](tools/README.md));
the automatic checks on pull requests need none of that. [AGENTS.md](AGENTS.md) is the
starting point for coding agents.

On Windows, clone with long paths enabled, because some Zero Hour reference
paths exceed 260 characters:

```sh
git clone -c core.longpaths=true <repository URL>
```

The earlier [Open-BFME-2](https://github.com/Open-BFME/Open-BFME-2) project
reports **100%** code byte matching and measures largely one-function source
files in its published phase-two baseline. Its
[2026-11-09 boot receipt](https://github.com/Open-BFME/Open-BFME-2/blob/master/docs/linking_obstacles/fx-module-class-eager-instances-2026-11-06.md)
records reaching the menu. This repository starts from shared definitions and
groups recovered functions into evidenced translation units: the earlier
project proved per-function byte matching, this one organises the result into
real source files. Its match count
uses the owned-function ledger shown above. The older project's percentage
measures executable code bytes.

## Known weaknesses

An independent, read-only review of the source on 2026-11-19 (80 files
sampled at revision `75d0188608`, graded on six axes) judged it ready to
show as a work in progress with real structural gains, but **not yet a
sound foundation**: ordinary gameplay files still make callers rebuild
pointer types and object contracts from casts. Its measurements:

- Of 40 files first graded the day before, 2 are good on all six axes and
  22 are poor on at least one (28 the day before). Of 40 newly sampled
  files, none is good on all six and 34 are poor on at least one. The
  weakest axes are comments (23 of the new 40 poor) and types (12 poor).
- 2,192 translation units are still named by address under `src/unk/`
  against 1,063 named units; 1,856 of the address-named units hold only
  comments and annotations, no code yet.
- 2,456 headers were provisional Drafts under `include/Draft/` against
  1,641 ordinary headers at that revision. Most Drafts are unused generated
  layout guesses; the [worklist](worklist/README.md) lists the ones in use
  separately.
- 852 declarations or definitions use `void *` and 5,169 use bare integer
  words in their signatures. These are lexical counts that include
  legitimate uses; the findings below are confirmed cases.

The ten findings, as the review stated them, and where each stands on
2026-11-20:

1. `include/Common/Vector.h` defined its own partial `_STL::vector` when
   STLport was absent, so one spelling selected two implementations.
   *Fixed:* the header now uses STLport only.
2. `AutoPickUpUpdate.cpp` hand-implements a partial vector and casts a
   pointer member to an allocator. *Open.*
3. `StealthDetectorUpdate.cpp` keeps a dead `if (0) { AsciiString unused; }`
   only to shape the compiler's exception-handling output. *Open.*
4. `AptScoreScreen::OpenScreen(int, int)` took an object and its input record
   as integers. *Partly fixed:* the record is typed now; the screen is still an
   address-named global.
5. `OneRingPenaltyUpdate.cpp` calls a numbered terrain virtual slot by reading
   the vtable through a cast. *Open.*
6. `texture.cpp` released a Direct3D texture through a raw COM slot.
   *Fixed:* it calls `Release()` on the interface.
7. `Transport` and `LANGameInfo` passed `void *` and `Int *` where the module
   knows the types. *Partly fixed:* `LANGameInfo` is typed; one `Transport`
   method still takes `void *`.
8. `SpecialPowerModuleData` declares `BitFlags<11>` for AntiCategory, while the
   project's own enumeration evidence gives 15 entries. *Open.*
9. `TunnelTracker.h` kept offset names for members whose roles its comments
   state. *Mostly fixed:* one offset-named member remains.
10. `W3DScene.cpp` holds network, object and subsystem methods with no stated
    reason for that placement. *Open.*

Each open item is a tracked issue in this repository.

Where to help: retiring the Drafts in use ([worklist/draft_headers_in_use.tsv](worklist/draft_headers_in_use.tsv)),
evidence that moves an address-named unit to its real file (see the
[worklist](worklist/README.md)), replacing stand-in types
([worklist/stand_in_types.tsv](worklist/stand_in_types.tsv)), and typed interfaces and real library
templates for the cases above ([source-quality rules](docs/source-quality.md)
on real types and real templates). A change that only raises the match
count while keeping a cast-based interface is not progress by these rules.

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
