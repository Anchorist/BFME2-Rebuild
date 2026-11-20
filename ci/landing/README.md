# Automatic landing

Nobody presses a merge button here. `.github/workflows/landing.yml` merges pull requests into `main`, one at a
time. The rules on `main` (`ruleset-main.json`) refuse every other route.

## When a pull request lands

- `BFME II / Boat` and `BFME II / source rules` passed on the pull request's exact latest commit, measured
  against the current `main`. When `main` has moved since, the workflow asks both checks to measure again and
  waits for them.
- `BFME II / Inline virtual` did not fail. It reports only for now, so pending is fine.
- It is ready for review (not a draft), merges cleanly, has no `landing-hold` label, and changes nothing under
  `.github/`.
- Pull requests from forks: the compiler check runs a new contributor's change only after a maintainer has read it
  and added the `boat-ok` label. Until then the pull request shows `Held: awaiting-admission`, and you do not need
  to do anything. Your branch name, title and description never decide anything.
- Changes under `include/` also need an approval from a header approver (below).

It lands as one squash commit, credited to you. The commit message says which `main`, head and tree were
measured. Afterwards the new commit is checked to have exactly that parent and that tree.

## Reading the result

Each pull request carries a `BFME II / Landing` status:

- `Landed as <commit>`: done. A comment says the same.
- `Cleared to land …`: it is being merged right now.
- `Held: <reason>. Expected <what is missing>.`: the reason and the next step. `pending` means waiting on
  someone else or on a check. `failure` means the pull request must change.

| Held reason | What to do |
|---|---|
| `awaiting-admission` | Nothing; a maintainer will look. |
| `awaiting-readmission` | Nothing; a maintainer reads your new commit and starts its compiler check. |
| `measuring` | Nothing; checks are running. |
| `check-failure` | Open that check's Details, fix, push. |
| `merge-conflict`, `merge-refused` | Merge or rebase `main` into your branch, push. |
| `header-approval` | Wait for a header approver. Every push needs a fresh approval. |
| `header-approvers-empty` | Header changes cannot land automatically yet. |
| `workflow-change` | A maintainer merges changes under `.github/` by hand. |
| `draft` | Choose Ready for review. |
| `head-changed`, `main-moved` | Nothing; the next run measures again. |

The Actions page shows one line per run (for example `Landed #9 as cd88e80ac175 …` or `Nothing to land …`). The
run summary has the table of every open pull request.

## Header approval

`header_approvers` in `landing.json` lists numeric GitHub account ids. An empty list means no change under
`include/` lands automatically.

- To add someone: `gh api users/<login> --jq .id`, then add that number to the list.
- What an approver does: open the pull request, go to **Files changed**, choose **Review changes**, select
  **Approve**, and submit. The approval counts only for the commit it was given on. After a new push, approve
  again.
- What the workflow checks: the latest review by any listed account is Approve, on exactly the current head. The
  pull request's own author never counts. A later Request changes by the same approver cancels their approval.

## Merge queue

Once `main` uses GitHub's merge queue, the workflow adds eligible pull requests to the queue instead of merging
them itself. See `MERGE-QUEUE.md`.

## Modes and tests

Scheduled and follow-up runs merge only when the repository variable `BFME_LANDING_MODE` is `live`. Otherwise
they report what they would do and change nothing. A manual run chooses `dry-run` or `live`, and can name one
pull request.

Tests: `python3 -m unittest discover -s ci/landing/tests -v` from the repository root.
