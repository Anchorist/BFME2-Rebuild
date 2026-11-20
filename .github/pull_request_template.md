<!-- One file, one Draft header or one function per pull request. Keep the Claim lines first. -->

Claim: src/path/File.cpp
<!-- or: Claim: include/Draft/X.h   or one line per function: Claim: 0x00ABCDEF -->

## What this changes

<!-- The functions or the header, in a sentence or two. -->

## Evidence

- Zero Hour counterpart (path:line), if one was used:
- Where the bytes in `baseline/game.dat` differ from Zero Hour, and which you followed:
- Names: where each new or changed name comes from (a string or export, the class's own virtual table,
  corresponding Zero Hour code). Unknown names stay placeholders.
- Inline or inherited virtuals you added or changed, with the slot they come from:
- What you could not confirm:

## Checklist (REVIEW.md)

- [ ] Real types: no `void *` or integer standing in for a type the code shows, no caller casting a value back
- [ ] One definition of every class, struct and global; a Draft I replaced is deleted and its includers moved
- [ ] Real templates and library code, no hand-written copies
- [ ] New comments say why; no addresses, dates or tags
- [ ] Only the claimed item changed; `// FUNCTION:` and `// cl:` lines untouched
- [ ] `Removed-Declaration:` lines in the commit message for every declaration I removed or renamed
