# Repository agent bridge

This file is intentionally short. The governing workflow is maintained in
[`Levtos/control`](https://github.com/Levtos/control), especially
[ADR 0002](https://github.com/Levtos/control/blob/main/docs/adr/0002-github-only-governance.md),
[ADR 0001](https://github.com/Levtos/control/blob/main/docs/adr/0001-ux-frontend-standard.md)
and the current binding GitHub issues.

## Repository scope

Each change in this repository is scoped to the explicitly assigned GitHub
issue and its acceptance criteria. Issue
[`blind_control#1`](https://github.com/Levtos/blind_control/issues/1) is the
bootstrap context for its own branch/PR; it is not a permanent repository
restriction. The sequenced AP1/AP2/AP3 work packages and their dependencies
are governed by [`control#31`](https://github.com/Levtos/control/issues/31)
and the current issue, so a later assigned issue may implement its own approved
policy, shadow, UX or cutover scope.

- Work from an isolated branch/worktree and keep unrelated cleanup out of the
  assigned issue.
- Use GitHub Issues, PRs, comments, ADRs and `Levtos/control/docs/` as the
  active governance and evidence source.
- Do not infer missing ownership, contract, migration or safety decisions;
  document a blocker and stop when it materially changes the requested work.
- Live, Actuation, Cutover, Entity-Rename, `Live` and `Live Verified` remain
  separate gates; perform them only when the assigned issue and Benni's gate
  explicitly authorize them.
- Green local or CI checks are technical evidence, never `Live` acceptance.

Repository-local changes must follow the assigned issue's acceptance and
completion format and remain consistent with the current GitHub decisions.
