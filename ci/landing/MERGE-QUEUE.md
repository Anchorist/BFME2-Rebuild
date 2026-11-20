# Landing with GitHub's merge queue (public repository)

Not built yet. This is the design for when the repository is public and `main` can sit behind a ruleset with a merge
queue. Until then `.github/workflows/landing.yml` serializes landings itself.

## Why switch

The serialized job checks main right before it merges and checks the new commit afterwards. The merge call itself
cannot say "only if main is still X". GitHub's merge queue closes that gap on GitHub's side. It builds a temporary
`gh-readonly-queue/main/...` commit of the current main plus the pull request. It runs the required checks on
exactly that commit. It moves main to exactly that commit only if they pass. Nothing else can move main while the
ruleset is active.

## Settings (Settings → Rules → Rulesets, target `main`)

- Require a pull request, one approval, and dismissal of stale approvals.
- Require status checks `BFME II / Boat` and `BFME II / source rules`. Add `BFME II / Inline virtual` only when it
  stops being report-only.
- Require the merge queue: merge method squash, build concurrency 1, group size 1 at first, status timeout 30
  minutes (wide changes measured 744 to 978 s).
- No bypass actors. Header changes: a CODEOWNERS entry `include/ @<maintainers>` with "require review from code
  owners" replaces `header_approvers`.

## Workflow changes

1. `managed-pr.yml` and `rules.yml` also run on `merge_group: types: [checks_requested]`. For that event the
   protected base is `github.event.merge_group.base_sha`, and the candidate tree is the tree of
   `github.event.merge_group.head_sha`. The tools and checkers still come from the base commit, never from the
   queue commit. The queue commit is data. A group that changes protected paths fails with its rule name.
2. Statuses are posted on the group's head SHA (`merge_group.head_sha`), with the same context names.
3. Contributors keep their exact-head checks on `pull_request_target`, so they see results before queueing.
4. `landing.yml` is reduced to adding eligible pull requests to the queue (GraphQL `enqueuePullRequest`, with the
   expected head). It keeps the branch-name refusals and the report comment. It no longer merges or re-measures.
5. The `push` trigger of `state.yml` fires for queue merges as usual. `bfme-landed` is no longer needed.

## Throughput

With group size 1 the queue is serial like today's job: about 11 landings an hour for one-file changes. With group
size N the queue tests N pull requests together and lands all of them when the group passes. A failing group is
split and retested. Raise N only after the check workflows have run against queue commits for a week.

## Live proof before switching

Open one good one-function pull request and one that changes a protected path. Queue both. The good one lands as
exactly the queue commit. The refused one leaves the queue with its rule name, and main does not move.
