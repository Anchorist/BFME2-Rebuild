# Approval policy

Deterministic: a pull request lands or it does not, decided by machine checks. No model is part of the
decision. An automatic approver may comment the result of this policy; nothing depends on its status.

## Lands with no person

All of these hold for the pull request's current head, checked against current `main`:

1. Every required check passed: the match check (compiles; no lost MATCH, reference proof or
   verified object), the text rules, and the virtual-behaviour check.
2. Every changed path is under `src/` or `include/`; nothing under `config/`, `expected/`,
   `baseline/`, `reference/`, `tools/`, `ci/`, `.github/`, `docs/` or a root file changes.
3. Nothing under `include/` changes.
4. It is not selected for sampling (below).

## Needs a person

- Any change under `include/`.
- One pull request in ten, chosen by the published sampling rule: the SHA-256 of a fixed policy label,
  the repository id and the pull request number, modulo 10. The same pull request is always selected
  or never, whatever its content or author.
- Anything a required check could not run on.

## Form

An approver that comments ends with one line: `APPROVAL: YES` or `APPROVAL: NO <rule>` (for example
`APPROVAL: NO include`, `APPROVAL: NO sampled`, `APPROVAL: NO check-failed`).
