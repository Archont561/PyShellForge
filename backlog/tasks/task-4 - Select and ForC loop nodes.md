---
id: task-4
title: Add Select and ForC loop nodes
status: To Do
labels: [ast, feature]
created_date: 2026-11-09
dependencies: []
references: [src/pyshellforge/ast/loops.py]
---

## Description

`For` and `While` cover the common cases. `select` and `for (( ... ))` are the
two remaining Bash loop forms users ask for, and both render as compound nodes.

## Acceptance criteria

- [ ] `Select` renders `select name in words; do ...; done`.
- [ ] `ForC` renders `for (( init; condition; step )); do ...; done`.
- [ ] Both reject cleanly in the POSIX backend.
- [ ] Both appear in `docs/reference/api-reference.md` and the README feature
      table.
- [ ] Validation rejects an empty body and invalid loop variables.

## Definition of done

- [ ] Gherkin scenario plus unit tests and a golden file.
- [ ] `pixi run automation check` green.
