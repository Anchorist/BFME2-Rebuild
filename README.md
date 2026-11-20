# The `state` branch

This branch is written only by the workflow `.github/workflows/state-publish.yml` on `main`.
Do not edit it by hand and do not open pull requests against it. Each commit describes one
commit of `main`; its subject is `State for main <commit>`. Its date is that main commit's date.

| Path | What it holds |
| --- | --- |
| `index.json` | `main` (the commit measured), `tree`, `checker` (digest of the comparison tools), `totals`, and `files`: the SHA-256 of every per-file record below |
| `files/<source path>.json` | one record per source file under `src/` that has an `expected/` record |

A per-file record:

```json
{"schema": 1, "tu": "src/Code/.../Example.cpp", "verified": true, "error": false,
 "gate_sha256": [],
 "functions": {"0x0012ABCD": ["MATCH", 100, true], "0x0012AC00": ["PARTIAL", 87.5, false]}}
```

- `functions` maps each function address (relative to the program's base, eight hex digits) to
  `[verdict, percent, proven]`. Verdicts: `MATCH`, `PARTIAL`, `MISSING`, `MISNAMED`,
  `WRONG_REFERENCE`, `COMPILE_ERROR`, `UNKNOWN_RVA`. `proven` is true only for a credited `MATCH`
  whose proof the checker accepted.
- `verified`: the whole compiled object agreed with the original. `error`: the file did not compile.
- `gate_sha256`: fingerprints of source-rule findings in the file (empty when there are none).

A record does not name the main commit, so a file whose verdicts did not change keeps identical
bytes from one commit to the next. To read the state of any past main commit, find the commit
whose subject names it (`git log state --grep "State for main <commit>"`).
