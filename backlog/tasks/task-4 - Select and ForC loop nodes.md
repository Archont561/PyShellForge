---
id: task-4
title: Add Select and ForC loop nodes
status: To Do
labels: [ast, feature]
created_date: 2026-11-09
dependencies: [task-11]
references: [docs/concepts/version-only-scaffold.md]
---

## Description

`select` and `for (( ... ))` are the two Bash loop forms left once roadmap
phase 2 lands the basic `for` and `while` nodes. Both are compound nodes, and both
need the node base that `task-11` adds.

## Acceptance criteria

- [ ] `Select` renders `select name in words; do ...; done`.
- [ ] `ForC` renders `for (( init; condition; step )); do ...; done`.
- [ ] Both reject cleanly in the POSIX backend.
- [ ] Both appear in `docs/reference/api-reference.md`.
- [ ] Validation rejects an empty body and invalid loop variables.

## Files

- `packages/pyshellforge/src/pyshellforge/ast/loops.py`

## Definition of done

- [ ] Gherkin scenario plus unit tests and a golden file.
- [ ] `pixi run automation check` green.
