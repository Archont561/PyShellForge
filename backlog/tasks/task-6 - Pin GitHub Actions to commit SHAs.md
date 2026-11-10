---
id: task-6
title: Pin GitHub Actions to commit SHAs
status: To Do
labels: [ci, security]
created_date: 2026-11-09
dependencies: []
milestone: m-5
references: [.github/workflows/ci.yml, .github/workflows/pixi-sandbox.yml, .github/workflows/release.yml, docs/development/tooling.md]
---

## Description

The workflows currently reference actions by major version tag (`@v4`, `@v5`).
The Archont561 convention is to pin every action to a full commit SHA with the
version in a trailing comment, so a moved tag cannot change what CI runs.

`release.yml` already pins all three of its actions; `ci.yml` and
`pixi-sandbox.yml` still carry 17 floating tags between them.

## Acceptance criteria

- [ ] Every `uses:` in `.github/workflows/` is pinned to a 40-character commit
      SHA with a `# vX.Y.Z` comment.
- [ ] Dependabot or a scheduled job keeps the pins current.
- [ ] `actionlint` still passes and the workflows run green once.

## Definition of done

- [ ] Both workflows updated; CI green.
- [ ] `docs/development/tooling.md` documents the pinning rule.
