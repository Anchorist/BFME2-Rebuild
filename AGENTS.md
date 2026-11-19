# AGENTS.md

Goal: rebuild the Battle for Middle-earth II engine (`game.dat` 1.06) as readable C++ that compiles, with the original
compiler, to the original machine code.

## Where things live

| Path | What it is |
|---|---|
| `src/` | source files; `src/unk/O<addr>.cpp` are files whose original name is not yet known |
| `include/` | shared headers; `include/Draft/` are unverified layouts, used only until a real header exists |
| `config/map.json` | the ledger: every function and data item of the original, with address, name, owner file, status |
| `expected/` | generated check records; do not edit |
| `baseline/game.dat` | the original program; read it for the bytes of any function |
| `reference/` | Zero Hour source (the predecessor game); a guide, never compiled |
| `worklist/` | what to do next, regenerated from `main` |
| `docs/` | rules with examples, recipes, known dead ends |
| `tools/`, `ci/` | the checker and the pull-request check; do not edit |

## The work

1. Finish a file (`worklist/files.tsv`) or write a missing function (`worklist/unwritten_with_zero_hour_counterpart.tsv`).
2. Replace a Draft header that is in use with a real one: `worklist/draft_headers_in_use.tsv`.
3. Identify an address-named file: show which original source file `src/unk/O<addr>.cpp` is.
4. Supply evidence for a name, a type, a class layout or a virtual-table order: open issues.
5. Record a dead end in `docs/hard_rows.md`.

## One item, start to finish

1. Pick one unclaimed file or Draft. Claim it: a draft pull request with `Claim: src/path/File.cpp` (or an address).
2. Read the function's bytes in `baseline/game.dat` at its address. Read the Zero Hour counterpart in `reference/`.
   Where they disagree, the bytes are right.
3. Write it in the file the ledger names, against the shared headers.
4. Push. The check **BFME II / Boat** compiles it and compares it with the original; read its report.
5. Fix from the report, three rounds at most. Then either it passes, or you record the dead end and release the claim.

## Rules

- One definition of every class, struct and global. Replacing a Draft: move every includer, delete the Draft.
- Real types. No `void *` or integer standing in for a type the code shows.
- Names from evidence: a string or export in the original, the class's own virtual table, or Zero Hour where the code
  corresponds. Unknown stays a placeholder.
- An inline virtual's behaviour comes from the original's table slot for that class.
- Change only `.c`/`.cpp` under `src/` and headers under `include/`. No new files, no moving functions between files.
- Leave `FUNCTION` annotation lines exactly as they are.
- No inline assembly, emitted bytes, pragmas or casts used to force a match.
- Comments say why. No addresses, dates or author tags.
- Nothing may stop matching that matched before.

## Done

A function is finished when it matches, its references are proven, its file has a real name and its class has a real
header. Details: `CONTRIBUTING.md`.
