# Header rules

A pull request that changes anything under `include/` gets one status, `BFME II / Header rules`. It is computed
from eight rules by `.github/workflows/header-rules.yml`, using `collect.py` and `compose.py`, on GitHub-hosted
runners.

| Rule | What it checks |
|---|---|
| H1 | The wide comparison: every unit that includes a changed header still matches as before. |
| H2 | Every declaration you add or change compiles to the exact name the ledger holds. A missing name becomes a ledger request (H9). |
| H3 | Nothing is defined twice under the same qualified name. |
| H4 | A removed or renamed declaration is named in a `Removed-Declaration:` line of your last commit, and nothing still uses it. |
| H5 | A changed size, offset, base or virtual slot order is paid for by a newly matched function that uses it. |
| H6 | An inline function body in a header is simple, or its behaviour is proven. |
| H7 | A Draft replaced by a real header is deleted, with every includer moved. |
| H8 | The source rules for headers: no forcing constructs, no growth of stand-in types. |

The status reads:

- `Header rules passed (main …)`: all eight passed on this exact commit and `main`.
- `H<n>: …`: that rule needs a change from you. The run summary says where and what to do.
- `Held: ledger request …`: your change needs a new name or size in the ledger. It waits for that decision and
  never fails.
- `Held: rule not built: …`: a rule's check is not running yet. Nothing passes on a rule that is not built.
- `Held: H<n> …`: that rule is still collecting its proof.

The pull request's files are fetched as Git objects in a step that has no token, and nothing from them is run.

Tests: `python3 -m unittest discover -s ci/header/tests -v` from the repository root.
