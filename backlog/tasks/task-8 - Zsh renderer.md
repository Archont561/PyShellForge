---
id: task-8
title: Zsh renderer
status: To Do
labels: [renderer, shells]
created_date: 2026-11-09
dependencies: [task-2, task-11]
references: [docs/concepts/version-only-scaffold.md]
---

## Description

Zsh accepts nearly all Bash syntax, so the renderer is a thin subclass of
`BashRenderer` that changes the shebang, drops `set -euo pipefail` for the
equivalent `setopt` line where they differ, and fixes the places where Zsh is
stricter: unquoted `$var` splits differently, `=~` uses `REMATCH`, and `local`
needs declaring.

## Acceptance criteria

- [ ] `ZshBackend` registered under `zsh` in `backends/__init__.py`, exposed by
      `psf render --shell zsh`.
- [ ] Every example renders, and `zsh -n` passes for each in an integration test
      (skipped when `zsh` is absent).
- [ ] The capability matrix in `docs/reference/backends.md` gains the Zsh column and
      the caveats found while testing.

## Files

- `pyshellforge/src/pyshellforge/backends/__init__.py`
- `pyshellforge/src/pyshellforge/renderers/zsh.py`

## Definition of done

- [ ] Tests green in CI with `zsh` installed, snapshot files added, `CHANGELOG.md`
      entry.
