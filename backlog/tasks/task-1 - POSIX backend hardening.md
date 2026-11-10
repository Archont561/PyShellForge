---
id: task-1
title: POSIX backend hardening
status: To Do
milestone: m-1
labels: [backend, posix]
created_date: 2026-11-09
dependencies: [task-11]
references: [pyshellforge/src/pyshellforge/__init__.py, .github/workflows/ci.yml]
---

## Description

The POSIX backend is where the portable subset is defined: what it can express,
what it rewrites, and what it refuses rather than silently downgrade. Nothing
implements it yet, so this task waits on `task-11` for the AST and the Bash
renderer it diverges from.

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

- [ ] Scenarios in `pyshellforge/features/` cover the accept and reject paths.
- [ ] Tests pass: `pixi run automation test-all`.
- [ ] Coverage gate passes: `pixi run automation coverage-all`.
- [ ] Documentation updated and `pixi run automation check-docs` passes.
- [ ] CHANGELOG entry added under `Unreleased`.

## Files

- `pyshellforge/src/pyshellforge/backends/posix.py`
- `pyshellforge/src/pyshellforge/renderers/posix.py`
- `docs/reference/backends.md`, the capability matrix every renderer extends

## Notes

The golden-file strategy that `task-3` sets up for `bash -n` carries over to
`sh -n` unchanged.
