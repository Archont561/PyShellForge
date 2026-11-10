---
id: task-1
title: POSIX backend hardening
status: In Progress
milestone: m-1
labels: [backend, posix]
created_date: 2026-11-09
dependencies: []
references: [src/pyshellforge/backends/posix.py, src/pyshellforge/renderers/posix.py]
---

## Description

The POSIX backend renders a `/bin/sh` subset but still needs a full audit of
what it emits and how it refuses what it cannot express.

## Acceptance criteria

- [ ] Every node has a documented POSIX decision: implemented, rewritten, or
      rejected with `UnsupportedNodeError`.
- [ ] `[[ ... ]]` and other Bash-only constructs are rejected, not silently
      downgraded.
- [ ] `local` is rendered only where the target shell supports it, and the
      limitation is documented.
- [ ] Rendered POSIX scripts pass `sh -n` for every example in CI.
- [ ] `docs/reference/backends.md` lists the supported subset.

## Definition of done

- [ ] Scenarios in `features/product/` cover the accept and reject paths.
- [ ] Tests pass: `pixi run automation test-all`.
- [ ] Coverage gate passes: `pixi run automation coverage-all`.
- [ ] Documentation updated and `pixi run automation check-docs` passes.
- [ ] CHANGELOG entry added under `Unreleased`.

## Notes

Start from `tests/integration/test_bash_syntax.py`: the same golden-file strategy
works for `sh -n`.
