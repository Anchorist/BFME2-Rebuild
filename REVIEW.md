# Review checklist

For any reviewer, automatic or human, and for people sampling. Apply it to the pull request's diff
only. Advisory: it decides nothing. What decides is the deterministic machine checks (the match check, the text
rules and the virtual-behaviour check); a reviewer comments, it never approves, merges or edits.

## How to answer

Give every item `PASS`, `FAIL` or `N/A`, each with one line of reason that cites `file:line` for a FAIL.
End the comment with exactly one verdict line, alone on its line, in this form:

    REVIEW-VERDICT: PASS
    REVIEW-VERDICT: FAIL R2,R5

`FAIL` lists the failed item numbers, comma-separated, no spaces. The verdict is `PASS` only when no
item is `FAIL`. A script reads the last line that starts with `REVIEW-VERDICT:`.

## Items

**R1 Real types.** No `void *`, integer word or cast stands in for a type the code shows (a pointer
stored in `int`, a caller casting a return value back, a struct read through raw offsets when the
type is declared). FAIL if the diff adds one; an existing one it does not touch is N/A.

**R2 Names from evidence.** Every new or changed name of a function, method, member or type comes from
evidence for that class: a string or export in `baseline/game.dat`, the class's own virtual table, or
Zero Hour code that corresponds. The pull request says which. An unknown stays a placeholder or an
offset name. FAIL on a name borrowed from another class or invented without stated evidence.

**R3 One definition.** The diff adds no second definition of a class, struct, enum or global that
already exists anywhere under `include/` or `src/`, under any name. Promoting a Draft moves every
includer and deletes the Draft in the same change.

**R4 Real templates and library code.** Containers, strings and algorithms use the real STLport or
engine templates. FAIL on a hand-written copy of library code or a container's internals.

**R5 Comments say why.** New comments give evidence or intent. FAIL on addresses or byte counts
repeated from the ledger, dates, author or tool tags, attempt notes, or "matches retail" remarks.

**R6 Nothing outside the item.** Every changed line serves the claimed file, Draft or function
(`Claim:` lines in the description). No unrelated reformatting, renames or moves; no new source files (a new header only
when it replaces a Draft); no function moved between files; `// FUNCTION:` annotation lines and `// cl:` lines unchanged; only `.c`/`.cpp` under `src/` and
headers under `include/`.

**R7 Reads as source.** A maintainer can follow the code without the disassembly: ordinary control
flow, named locals, no dead statements or declarations kept only to steer the compiler, no
`__asm`, emitted bytes or pragmas.

**R8 Inline virtuals.** Any inline or inherited virtual the diff adds or changes states, in a comment,
its slot in the class's virtual table in `baseline/game.dat` and the behaviour that slot shows.
FAIL if the return value or behaviour is a default with no slot evidence.

**R9 Evidence stated.** The pull request description names the Zero Hour counterpart if one was used,
what differs from it, and anything not confirmed. Where Zero Hour and `baseline/game.dat` disagree,
the code follows `baseline/game.dat`.

## Example

    R1 PASS  m_owner is Object *, as in Object.h.
    R2 FAIL  include/GameLogic/Foo.h:40 names slot 12 "update" with no evidence for Foo.
    R3 PASS
    R4 N/A
    R5 FAIL  src/.../Foo.cpp:88 comment repeats the address and size.
    R6 PASS
    R7 PASS
    R8 N/A
    R9 PASS  Zero Hour Foo.cpp:210 cited; the extra null test follows the bytes.
    REVIEW-VERDICT: FAIL R2,R5

The full rules with examples are in [docs/source-quality.md](docs/source-quality.md).
