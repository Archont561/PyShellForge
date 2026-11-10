---
id: task-16
title: DSL surface, the first wave
status: To Do
labels: [ast, feature]
created_date: 2026-11-10
dependencies: [task-11]
references: [packages/pyshellforge/src/pyshellforge/__init__.py, docs/concepts/version-only-scaffold.md]
---

## Description

Three constructs that a deployable script cannot do without, and that change the
shape of the tree, so they come before the language-y parts rather than after.

Parameter expansion is the important one. Real scripts are a third `${V:-default}`
and `${V%%.*}`; without a node for them a user reaches for a raw string, and a raw
string is where quoting guarantees and every later rule stop working. Redirections
belong on the command node as an attribute, not as a node of their own. Script
options (`set`, `umask`, `trap`) are placement decisions the backend has to own,
because only it knows what the preamble looks like.

Wave two, which covers pipelines, `case`, arrays and heredocs, follows with the capability flags
of `task-17`. Refused outright: `eval`, backticks, `$*`, `select` and `coproc`.

## Files

- `packages/pyshellforge/src/pyshellforge/ast/nodes/expansion.py` for `Expand` and its kinds
- `packages/pyshellforge/src/pyshellforge/ast/nodes/command.py` for the redirect attribute
- `packages/pyshellforge/src/pyshellforge/ast/nodes/settings.py` for `set`, `umask` and `trap`
- `docs/reference/api-reference.md` for the surface
- `packages/pyshellforge/features/` for the scenarios

## Acceptance criteria

- [ ] `Expand` covers `${V}`, `${V:-w}`, `${V:=w}`, `${V:?w}`, `${V:+w}`, `${#V}`,
      `${V#p}`, `${V##p}`, `${V%p}`, `${V%%p}` and `${V/a/b}`, and each renders
      with the variable quoted inside the braces.
- [ ] A redirect carries an optional file descriptor and an operator, so `2>`,
      `>>` and `2>&1` render without a raw string.
- [ ] `set -euo pipefail` stays a backend decision: a user can add options but
      cannot remove strict mode by accident.
- [ ] `trap` renders where the backend places it, and a POSIX target refuses
      `pipefail` instead of emitting it.
- [ ] Every new node has a golden file and a `bash -n` check.
- [ ] `docs/reference/api-reference.md` documents each node with its rendering.

## Definition of done

- [ ] Unit tests per node and per expansion kind, including an empty value and a
      value with a quote in it.
- [ ] A Gherkin scenario for the expansion family.
- [ ] The roadmap row for phase 2 says what landed.
