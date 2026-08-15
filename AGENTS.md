# Repository agent bridge

This file is intentionally short. The governing workflow is maintained in
[`Levtos/control`](https://github.com/Levtos/control), especially
[ADR 0002](https://github.com/Levtos/control/blob/main/docs/adr/0002-github-only-governance.md)
and the binding decision
[`control#31`](https://github.com/Levtos/control/issues/31).

## Issue scope

The only implementation scope in this repository is
[`blind_control#1`](https://github.com/Levtos/blind_control/issues/1): AP1
bootstrap, inventory, owner/contract matrix, and migration boundaries.

- Work from an isolated branch/worktree.
- Keep AP1 non-actuating and local-first.
- Do not add cover services, entity renames, live changes, or policy-engine
  assumptions.
- Treat green local checks as technical evidence, never as `Live` acceptance.
- Keep unresolved owner/freshness decisions explicitly open instead of guessing.

Repository-local changes must follow the issue's required Abschlussformat and
remain consistent with the control repository's ADRs and current GitHub
issues/comments.
