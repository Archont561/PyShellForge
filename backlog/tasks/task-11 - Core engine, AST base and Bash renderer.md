---
id: task-11
title: Core engine, AST base and Bash renderer
status: To Do
labels: [ast, renderer, core]
created_date: 2026-11-10
dependencies: []
references: [pyshellforge/src/pyshellforge/__init__.py, pyshellforge/pyproject.toml, docs/concepts/version-only-scaffold.md, docs/development/testing.md]
---

## Description

The first slice of roadmap phase 1, and the root of the dependency graph: a
backend cannot diverge from Bash before a Bash renderer exists, and a plugin
contract cannot be documented before the registry it plugs into.

Three nodes wide on purpose. Comments, variable assignments and commands render a
real script end to end, and they force the decisions everything later inherits:
how a node describes itself, how a renderer dispatches on it, how a literal is
quoted, and how a construct the target cannot express fails.

## Files

- `pyshellforge/src/pyshellforge/core/` for `ShellScript` and the node registry
- `pyshellforge/src/pyshellforge/ast/` for the node base and the three nodes
- `pyshellforge/src/pyshellforge/renderers/bash.py` for the renderer and the quoting helper
- `pyshellforge/src/pyshellforge/ast/nodes/echo.py` for `Echo` and the interpolation kinds
- `docs/concepts/ast-design.md` for why the tree has this shape
- `docs/reference/api-reference.md` for the public surface
- `pyshellforge/features/` for the scenarios, once the first node lands

## Acceptance criteria

- [ ] `ShellScript` collects nodes and renders through a renderer object,
      `ShellScript(renderer=BashRenderer())`, as decision-1 describes.
- [ ] The node base carries what a renderer needs and nothing that belongs to one
      shell.
- [ ] `Comment`, `VariableAssignment` and `Command` render to canonical Bash: one
      construct per line, four-space indentation, no trailing whitespace.
- [ ] One helper quotes every literal, and it is the only place that picks between
      bare text, single quotes and escaping.
- [ ] A node the target cannot express raises `UnsupportedNodeError`, naming the
      node and the target.
- [ ] `Echo` renders `printf '%s\n'` with one double-quoted argument, because
      `echo` varies by shell and mangles text that begins with a dash.
- [ ] In an interpolation, a declared name becomes `${NAME}` and never `$NAME`,
      literal text escapes backslash, double quote, dollar and backtick, and a
      name that is not declared fails with a stable diagnostic.
- [ ] A format spec or a conversion in an interpolation is refused, and `!q`
      renders as a runtime quote.
- [ ] Rendered output parses: the suite runs `bash -n` over every golden script.

## Definition of done

- [ ] Unit tests per node, tests for the quoting helper, and golden files.
- [ ] One execution test that renders and runs `bash -n` on the result.
- [ ] A Gherkin scenario in `pyshellforge/features/` with its step module.
- [ ] Both documentation pages exist, `docs/README.md` links them, and
      `pixi run automation check-docs` passes.
- [ ] `pixi run automation check` and `pixi run automation coverage-all` pass.
- [ ] `CHANGELOG.md` records the slice under `Unreleased`, and the phase 1 row of
      the roadmap says what landed.
