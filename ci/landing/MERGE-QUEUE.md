# Landing with GitHub's merge queue

The landing workflow already supports the merge queue. It reads main's active rules on every run
(`GET /repos/{repo}/rules/branches/main`):

- No `merge_queue` rule (today, and while the rules cannot be read): it merges directly. It measures again on
  current main when needed, re-reads main right before the merge, and verifies the new commit.
- A `merge_queue` rule is active: it adds each eligible pull request to the queue with its expected head
  (GraphQL `enqueuePullRequest`, `expectedHeadOid`). GitHub then measures main plus that pull request on a queue
  commit (`merge_group`) and merges exactly the commit it measured. The workflow no longer merges or re-measures.

The hold rules are the same in both modes: admission, header approval, rehearsal branches, `.github/` changes,
drafts and the `landing-hold` label.

## Who can move main

main carries two rulesets.

- A ruleset with no force-push and no deletion, and no bypass for anyone.
- The landing ruleset, separate because a bypass covers every rule in its ruleset: `ruleset-main.json` (direct)
  or `ruleset-main-queue.json` (queue). Changes only through pull requests (squash). Required statuses, each from
  GitHub Actions (integration 15368): `BFME II / Boat`, `BFME II / source rules` and `BFME II / Landing`. One
  named maintainer may bypass this ruleset only.

Only the landing workflow writes `BFME II / Landing` success:

- Direct mode: "Cleared to land on main X", on the exact head, immediately before it merges. It is withdrawn on
  any hold.
- Queue mode: "Cleared for the merge queue at head X" on the pull request, then "Cleared in the merge queue" on
  the queue commit. The workflow's `group` job (event `merge_group`) writes the second only when it queued that
  exact head itself. A pull request a person adds to the queue is refused there and leaves the queue.

So neither the merge button nor "Merge when ready" can move main for a pull request this workflow did not clear.
The only exception is the bypass account named in the ruleset.

## What the check workflows need (owners: managed-pr.yml and rules.yml)

Agreed contract: `merge_group: types: [checks_requested]`. Check out the tools from
`github.event.merge_group.base_sha`, never from the queue commit. Read the queue head
(`merge_group.head_sha`, ref `merge_group.head_ref`) as data only. Compare base to queue head. Post the same
contexts on `head_sha`. No landing receipts.

The ordinary pull-request checks stay required before a pull request may be queued. This matters: for `merge_group`
runs, GitHub takes the workflow file from the queue commit, so a pull request that changes `.github/` or `ci/` must
never reach the queue. The path refusal on the ordinary check, which is required, guarantees that.

## Batch size

Start strictly serial: `max_entries_to_build: 1` and `max_entries_to_merge: 1`.

- With build concurrency above 1, entry N+1's queue commit also contains entry N's change, while `base_sha` stays
  main. The source rules' per-pull-request path and scope limits (G1, G6) would then judge several pull requests
  as one.
- Serial throughput: a one-file check takes 3 to 4 minutes, so about 15 to 20 landings an hour. A header-sized
  check takes 12 to 16 minutes, so about 4 an hour while one is at the front. The direct mode measured 2 min 15 s
  to 2 min 42 s per one-file landing.
- Raise `max_entries_to_build` to 3 only after both check workflows judge each queued pull request on its own
  delta. That gives about 45 an hour when all pass. A failure rebuilds the entries behind it, so keep the depth
  small while the failure rate is high. Keep `max_entries_to_merge` at 1, so every pull request stays one squash
  commit credited to its author.
- `check_response_timeout_minutes: 30` covers the measured 744 to 978 s wide checks.

## Switch-over with no gap

1. Direct mode, the landing workflow merging: the no-force-push/no-deletion ruleset, plus the landing ruleset
   created with `gh api -X POST repos/Open-BFME/BFME2-Rebuild/rulesets --input ci/landing/ruleset-main.json`.
   The landing workflow keeps merging, and the rulesets refuse every other way in.
2. Install the `merge_group` handlers of `managed-pr.yml` and `rules.yml`. Nothing fires until the queue rule
   exists.
3. The switch itself produces the first real `merge_group` event, because the checks accept main only. It fails
   closed: an unexpected queue payload or ref gets a failure status, the entry leaves the queue, and main does not
   move. Watch the first queued pull request, and roll back (step 6) at the first unexplained refusal.
4. Switch the landing ruleset only, one API call that replaces its rules at once:
   `gh api -X PUT repos/Open-BFME/BFME2-Rebuild/rulesets/<landing ruleset id> --input
   ci/landing/ruleset-main-queue.json`. The no-force-push/no-deletion ruleset is never touched.
   - The next landing run sees `merge_queue` and enqueues.
   - A direct merge already in flight at that instant is refused by GitHub (HTTP 405). It is held with a named
     reason and queued on the next run.
   - Nothing lands outside the rules at any point, and no landing route is missing at any point.
5. Proof: one good pull request lands as exactly its queue commit. A pull request added to the queue by hand
   leaves it with `Held: not-queued-by-landing`. Main does not move for it.
6. Rollback: the same PUT to the landing ruleset with `ruleset-main.json`.

## Header approval in the queue

Unchanged: the workflow checks it before queueing, and only workflow-queued pull requests pass the queue commit's
`BFME II / Landing`.
