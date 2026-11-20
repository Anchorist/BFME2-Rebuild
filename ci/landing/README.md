# Automatic landing

`.github/workflows/landing.yml` merges pull requests into `main` one at a time. Nothing else moves `main`.

A pull request lands when all of these hold:

- `BFME II / Boat` and `BFME II / source rules` are success on the pull request's exact head, measured against
  the current `main` (the status text ends with `(main <first 12 characters of main>)`), and their protected runs
  left receipts that name the same main, head and merged tree.
- `BFME II / Inline virtual` is not failure. While it is report-only (`INLINE_VIRTUAL_POLICY` in `lander.py`),
  pending is allowed.
- It is open, not a draft, has no `landing-hold` label, merges cleanly, and does not change `.github/`.
- If it changes anything under `include/`, a person listed in `header_approvers` in `landing.json` approved this
  exact head. The pull request's author cannot approve their own change. An empty list means no header change lands
  automatically.
- Its branch does not start with `canary/`, `ci-corpus/` or `corpus/`. These are rehearsal and test-corpus branches.
  They never land. `rehearsal_exceptions` in `landing.json` can allow one exact pull request and head for a trial.

When the checks were measured against an older `main`, the job asks for a fresh measurement. When `remeasure` is
`repository_dispatch` it sends `bfme-remeasure` and waits. When `remeasure` is `off` the pull request waits for a
new push or a reopen.

Before merging, the job reads `main` again and stops if it moved. It merges with `squash` and the expected head
SHA, so the result is one commit per pull request credited to its author. It then checks that the new `main`
commit has exactly one parent, the measured main, and exactly the measured tree. If that check fails, the job marks
the commit with a failed `BFME II / Landing` status. No further pull request lands until a maintainer repairs
`main`.

If the merge outcome is unknown (the merge call timed out, its response was lost, or the job stopped), the commit
message the job gave the merge still names the measured main, head and tree. The next run starts by looking at the
newest commit on `main`. If it is a landing commit without a `BFME II / Landing` status, the run checks its parent
and tree. It then marks the commit and sends the hand-off, or stops landing exactly as above. A dry run only
reports it.

Each pull request gets a `BFME II / Landing` status: `Landed as <commit>`, or `Held: <reason>`. A landed pull
request also gets a comment. After a landing the job sends `bfme-landed` for the workflows that refresh state, and
`bfme-land-next` to take the next pull request.

Modes: scheduled and follow-up runs merge only when the repository variable `BFME_LANDING_MODE` is `live`.
Otherwise they report what they would do and change nothing. A manual run chooses `dry-run` or `live`, and can
name one pull request.

Tests: `python3 -m unittest discover -s ci/landing/tests -v` from the repository root.
