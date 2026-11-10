---
id: task-17
title: Backend capability matrix and the PowerShell proof
status: To Do
labels: [renderer, backends]
created_date: 2026-11-10
dependencies: [task-11, task-1]
references: [docs/reference/repository-layout.md, backlog/tasks/task-8 - Zsh renderer.md, backlog/tasks/task-10 - Entry-point discovery for third-party renderers.md]
---

## Description

Two things a second backend needs before it can be written, and one experiment
that proves the plugin surface is real.

First, a `Backend` has to own more than a shebang and `set -euo pipefail`. It owns
the preamble (which may not exist), the artifact policy (encoding, line endings,
a minimum interpreter version) and a capability table. PowerShell is why: a
`.ps1` for version 5.1 needs UTF-8 with a byte-order mark and reads ANSI without
one, and `&&` needs version 7.

Second, the capability table has to be published, because "does this target
support arrays" is a question users ask and the answer is a gap list, not a
promise. `docs/reference/backends.md` is that table, and `task-8` and `task-9`
already assume `psf render --shell zsh` exists.

PowerShell is deliberately out of tree. It is the reference third-party renderer:
it proves that entry-point discovery works for a real non-Bash target, and it
keeps a backend with a different quoting model, a different command vocabulary
and an object pipeline from reshaping the node set that Bash needs.

## Files

- `docs/reference/backends.md` for the capability matrix
- `pyshellforge/src/pyshellforge/backends/` for the preamble, the artifact policy
  and the capability table
- `pyshellforge/tests/integration/` for the matrix and the refusal messages

## Acceptance criteria

- [ ] A backend declares a preamble, a capability set and an artifact policy, and
      the renderer reads all three instead of testing the shell name.
- [ ] The capability matrix has one row per node kind and one column per backend,
      with `yes`, `partial` or the refusal, and it is generated from the table
      rather than written twice.
- [ ] Refusing a construct names the node and the target, as
      `UnsupportedNodeError` already does.
- [ ] A PowerShell backend outside the package renders the three nodes of
      `task-11` and the `if` node, and the generated `.ps1` parses under
      `pwsh -NoProfile`, which runs on the Linux CI runner as well.
- [ ] The PowerShell backend is documented as a gap list: quoting, the command
      vocabulary and the object pipeline are its own, and semantic parity across
      shells is not claimed.

## Definition of done

- [ ] `docs/reference/backends.md` is linked from the index and lists every
      capability with its reason.
- [ ] A test fails when a backend claims a capability the matrix does not list.
- [ ] `CHANGELOG.md` records the backend contract under `Unreleased`.
