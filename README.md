# Battle for Middle-earth II engine rebuild

This project reconstructs the engine as maintainable source organized around the
reference build's translation units and shared headers. A translation unit
is one C or C++ source file together with the headers it includes. The
compiler produces one object file for each unit. The target is the game's
version 1.06 `game.dat`. The source should read like an ordinary engineering
project and compile to the reference code.

## Status

The maintainers recorded these progress counts at
**2026-11-19 17:05 UTC**, revision `e226a9b406` of their
working repository (the tree of this snapshot's `src/`, `include/`,
`config/` and `expected/` is that revision or a later one).

| Measure | At that snapshot |
| --- | ---: |
| Owned functions credited MATCH | 14,992 / 41,565 |
| Credited functions with proven references | 11,588 |
| Whole objects VERIFIED | 151 / 2,154 |
| Headers outside `include/Draft/` | 1,669 |
| Owned function names classified as real / placeholder | 23,544 / 18,021 |

36% of the owned functions had match credit at that snapshot.

Source files with code: **824 named** and **335 still named by
address** (under `src/unk/`, waiting for evidence of their real name and
place). Another 2,095 files hold only generated
annotations and no code yet (1,856 address-named, 239
named); they are scaffolds, counted apart.

In this snapshot's tree, **27 Draft headers are in use** (included by
some file; these are the ones to retire). Another 2,134 Drafts are
unused generated layout guesses: 2,118 are kept as leads for classes not
written yet and 16 are dead copies of headers that now exist outside
`include/Draft/`. See the [worklist](worklist/README.md).

See [the checker verdicts](docs/ledger-and-checks.md#read-the-verdict) for how
bytes, references, names and object verification are measured.

The game does not yet build from this source alone. A link of the rebuilt
objects on 2026-11-19 (run 15:36 UTC, revision `5c48db972b2e`)
still lacked 3,140 symbols and had
7 duplicate definitions.

In the project's 2026-11-18 substitution test, an executable used
**318 rebuilt translation units** alongside the remaining engine code
from the reference build. Its recorded simulation checksums agreed with
the reference build's on **40 of 40** compared frames on Udun, **200 of 200**
in the extended Udun run and **40 of 40 on Fords of Isen II**, and its
save-and-reload run passed. A deliberately perturbed control run diverged
at frame 500, so the comparison does detect a difference. A larger,
364-unit image from the same day did not yet produce comparable
checksums.

## Help rebuild the source

**Pull requests are not checked yet.** The automatic check is being
set up and outside pull requests are not admitted until it is. You can
already clone, read, choose an item, compare it with the public Zero Hour
source and open an issue with evidence. The [pull-request
guide](ci/README.md) describes how the check will work.

Start with the [worklist](worklist/README.md) and
[contribution guide](CONTRIBUTING.md). Good first contributions are a small
group of related functions, replacing a Draft header that is in use with a
real one, or evidence for a name or file assignment. A plain clone is
enough to choose an item, read the original bytes of any function in
`baseline/game.dat`, compare them with the public Zero Hour source and
request evidence. A local check additionally needs only the reference
compiler toolchain ([tools/README.md](tools/README.md)); it is optional. [AGENTS.md](AGENTS.md) is the
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
groups recovered functions into evidenced translation units. Its match count
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

The ten findings, as the review states them:

1. `include/Common/Vector.h` defines its own partial `_STL::vector` when
   STLport is absent, so one spelling selects two implementations.
2. `AutoPickUpUpdate.cpp` hand-implements a partial vector and casts a
   pointer member to an allocator.
3. `StealthDetectorUpdate.cpp` keeps a dead `if (0) { AsciiString unused; }`
   only to shape the compiler's exception-handling output.
4. `AptScoreScreen::OpenScreen(int, int)` takes an object and its input
   record as integers and casts them back, although both types are declared.
5. `OneRingPenaltyUpdate.cpp` calls a numbered terrain virtual slot by
   reading the vtable through a cast.
6. `texture.cpp` releases a Direct3D texture by calling COM slot 2 through a
   `void *` function type instead of the interface.
7. `Transport` and `LANGameInfo` pass `void *` and `Int *` where the module
   knows the types, and callers cast them back (one casts away `const`).
8. `SpecialPowerModuleData` declares `BitFlags<11>` for AntiCategory, while
   the project's own enumeration evidence gives 15 entries.
9. `TunnelTracker.h` keeps offset names for members whose roles its own
   comments state.
10. `W3DScene.cpp` holds network, object and subsystem methods with no
    stated reason for that placement.

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

See [LICENSE](LICENSE) and [NOTICE](NOTICE) for the GPL-3 terms and
third-party notices. The Electronic Arts GPL release and its additional
terms cover the text derived from that release. GameSpy SDK and EA PPMalloc
text retain their own notices and are outside this repository's GPL-3 licence
statement.
