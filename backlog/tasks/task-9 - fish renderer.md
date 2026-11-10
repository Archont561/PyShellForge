---
id: task-9
title: fish renderer
status: To Do
labels: [renderer, shells]
created_date: 2026-11-09
dependencies: [task-2, task-8, task-11]
milestone: m-4
references: []
---

## Description

fish is not Bourne-compatible, so this is the first renderer that cannot inherit
most of `BashRenderer`. Known shape differences: no prefix assignment
(`PATH=/x cmd`), `set -l`/`set -gx` instead of `local`/`export`, `(cmd)` instead
of `$(cmd)`, `test` instead of `[ ]`/`[[ ]]`, `$status` instead of `$?`,
`function f; end` blocks, and no heredocs.

## Acceptance criteria

- [ ] `FishRenderer` handles commands, variables, functions, `if`/`for`/`while`,
      pipelines and `&&`/`||` chains.
- [ ] Arguably unrepresentable nodes raise `UnsupportedNodeError` (arrays beyond
      `set -a`, `Matches`, heredocs) with the portable alternative in the message.
- [ ] Quoting gains a fish branch: single quotes cannot contain a single quote, so
      the helper escapes by closing and reopening the string or by using `\\`.
- [ ] `fish -n` and execution tests run in CI when `fish` is installed.

## Files

- `packages/pyshellforge/src/pyshellforge/renderers/fish.py`
- `packages/pyshellforge/src/pyshellforge/renderers/quoting.py`, the helper `task-11` adds
- `docs/reference/backends.md`, the capability matrix

## Definition of done

- [ ] Documented gap list on its own docs page, matrix updated, `CHANGELOG.md`.
