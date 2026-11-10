---
id: task-3
title: Verify rendered output with shfmt in CI
status: To Do
labels: [ci, tooling]
created_date: 2026-11-09
dependencies: []
references: [.github/workflows/ci.yml, tests/integration/test_bash_syntax.py]
---

## Description

`bash -n` proves the rendered scripts parse; `shellcheck` proves they are sane.
`shfmt --diff` would additionally prove the formatting is canonical, which is a
direct promise of the renderer.

## Acceptance criteria

- [ ] CI runs `shfmt -d -i 4 -ci` over every rendered example and fails on a
      diff.
- [ ] Snapshots are formatted with `shfmt` so the check is stable.
- [ ] `docs/development/testing.md` explains how to run it locally.

## Definition of done

- [ ] Failing check demonstrated in review (a deliberately misformatted script).
- [ ] Documentation updated.
