---
id: task-3
title: Verify rendered output with shfmt in CI
status: In Progress
labels: [ci, tooling]
created_date: 2026-11-09
dependencies: [task-11]
milestone: m-2
references: [.github/workflows/ci.yml, docs/development/testing.md]
---

## Description

`bash -n` proves the rendered scripts parse; `shellcheck` proves they are sane.
`shfmt --diff` would additionally prove the formatting is canonical, which is a
direct promise of the renderer.

## Acceptance criteria

- [ ] CI runs `shfmt -d -i 4 -ci` over every rendered example and fails on a
      diff.
- [x] Snapshots are formatted with `shfmt` so the check is stable.
- [x] `docs/development/testing.md` explains how to run it locally.

## Files

- `packages/pyshellforge/tests/integration/test_bash_syntax.py`

## Definition of done

- [x] A test demonstrates a failure on a deliberately misformatted script.
- [x] Documentation updated.

## Progress

The workflow installs the pinned formatter and checks the golden scripts. The
same check and the intentionally failing example pass locally; the CI run remains
to be verified before this task is done.
