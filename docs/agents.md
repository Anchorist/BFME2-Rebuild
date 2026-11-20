# Get your agents started

This page is for people who point AI coding agents at this repository. [AGENTS.md](../AGENTS.md) is the short brief the
agent reads by itself; this page is for you, and for the agent to read once.

## What an agent needs

- `git`, and a way to open pull requests (the `gh` command is enough).
  On Windows, clone with `-c core.longpaths=true`: some reference paths are long.
- `objdump` from binutils, to read the original program. Any disassembler
  that opens a 32-bit Windows program will do.
- No compiler, no Wine and no copy of the game. The checks compile on the
  project's machines and tell the agent what happened.

## The loop

1. **Pick one item.** A small function is the best first task: take a row of
   `worklist/unwritten_with_zero_hour_counterpart.tsv` with
   `ready_at_snapshot=yes`, `reference_kind=def`, `body_check=none-found` and
   a `size_bytes` under about 100. The newest lists are on the
   [`progress` branch](https://github.com/Open-BFME/BFME2-Rebuild/tree/progress).
2. **Make sure it is free.** Search the open pull requests for the address
   and the file. Search `src/` and `include/` for the address too: the list
   may be older than `main`.
3. **Read the original.** Each function has a `// FUNCTION:` line in the file
   that owns it, giving its address (an RVA) and size. Add `0x400000` to the
   RVA and disassemble that range:

   ```sh
   # FrameData::allCommandsReady: RVA 0x005DA563, size 75 (0x4B)
   objdump -d -M intel --start-address=0x9DA563 --stop-address=0x9DA5AE baseline/game.dat
   ```

4. **Read the counterpart.** The worklist row names the matching Zero Hour
   function under `reference/`. It is a guide to names, types and shape. Where
   it and the bytes disagree, the bytes are right.
5. **Write the function** directly below its `// FUNCTION:` line, against the
   shared headers, in ordinary C++.
6. **Open a draft pull request** whose description starts with the claim and
   the evidence, as in the [template](../.github/pull_request_template.md):
   `Claim: 0x005DA563` for one function, `Claim: src/path/File.cpp` for a file.
7. **Read the report and fix.** The checks answer on the pull request, usually
   in about four minutes for a one-file change. Allow three rounds. If it
   still does not match, record what you learned in
   [hard_rows.md](hard_rows.md), close the pull request and take another item.

When every check passes and the pull request is marked ready, it lands by
itself.

## From a fork

Your pull requests come from a fork. The source rules answer at once. The
compile check needs one of the project's machines, so it waits until the
maintainer admits the pull request with the `boat-ok` label; the pull request
says so while it waits. Nothing from a pull request is ever run, only
compiled, and the checks themselves always come from `main`.

## Running several agents

- One item for each agent, and one item for each pull request.
- Claim first, then work: the draft pull request is the claim. Two agents on
  the same function waste both.
- Keep header changes out of a first pull request. A change to a header that
  many files include is rebuilt and compared for all of them, takes twelve to
  sixteen minutes, and anything under `include/` waits for the maintainer.
- Start each agent from a fresh `main`. The repository changes many times a
  day.

## What gets a pull request refused

The report names the rule. The full list is in [RULES.md](../RULES.md); these
are the ones agents meet most:

- Inline assembly, emitted bytes, or pragmas and casts used to force a match.
- A `void *` or an integer standing in for a type the code shows.
- A second definition of a class, struct or global that already exists.
- A changed `// FUNCTION:` or `// cl:` line.
- A new file, a function moved between files, or a change outside `src/` and
  `include/`.
- A comment that carries an address, a date or an author tag.
- Anything that matched before and no longer does.

Do not paste disassembly dumps into the repository, an issue or a pull
request: describe the address, the size and what the code does.

## A longer first prompt

```text
You are contributing to an open rebuild of the Battle for Middle-earth II
engine. Read AGENTS.md, docs/agents.md, CONTRIBUTING.md and one of the files
listed in docs/reference-files.md.

Task: write one unwritten function.
1. From worklist/unwritten_with_zero_hour_counterpart.tsv choose a row with
   ready_at_snapshot=yes, reference_kind=def, body_check=none-found and
   size_bytes under 100. Check that no open pull request mentions its address
   and that src/ and include/ hold no body for it.
2. Disassemble it from baseline/game.dat (address = RVA + 0x400000) and read
   its Zero Hour counterpart under reference/.
3. Write the body below its FUNCTION line in the owning file. Real types, no
   casts to force a match, no inline assembly, no new files.
4. Open a draft pull request that starts with "Claim: <address>" and gives
   the evidence in the template's form.
5. Read the report from the checks. Fix and push, three rounds at most. If it
   passes, mark the pull request ready. If not, say what you learned and
   close it.
```
