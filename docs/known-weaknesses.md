# Known weaknesses

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
  layout guesses; the [worklist](../worklist/README.md) lists the ones in use
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

Where to help: retiring the Drafts in use ([worklist/draft_headers_in_use.tsv](../worklist/draft_headers_in_use.tsv)),
evidence that moves an address-named unit to its real file (see the
[worklist](../worklist/README.md)), replacing stand-in types
([worklist/stand_in_types.tsv](../worklist/stand_in_types.tsv)), and typed interfaces and real library
templates for the cases above ([source-quality rules](source-quality.md)
on real types and real templates). A change that only raises the match
count while keeping a cast-based interface is not progress by these rules.
