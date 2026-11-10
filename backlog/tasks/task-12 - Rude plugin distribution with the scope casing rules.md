---
id: task-12
title: Rude plugin distribution with the scope casing rules
status: In Progress
labels: [lint, plugins]
created_date: 2026-11-10
dependencies: []
milestone: m-1
references: [packages/pyshellforge-rude/pyproject.toml, packages/pyshellforge-rude/src/pyshellforge_rude/rules.py, packages/pyshellforge-rude/tests/test_rules.py, docs/reference/linting.md, .coveragerc]
---

## Description

The first thing in this repository that can be installed and used: a Rude plugin
that checks the casing conventions a definition has to keep, as decision-6
describes. It needs no renderer, which is why it ships ahead of `task-11`.

A module-level binding in a definition becomes a global shell variable and a
binding inside a function becomes a `local`, so the case of a name is the only
place a reader can see which one it is. `PSF201` and `PSF202` enforce one half of
that pair each.

The distribution is `packages/pyshellforge-rude/`, mirroring the layout of
`Archont561/rude-clean-code`. The rules read the semantic model of Rude instead of
columns, so imports, class bodies, `global` declarations, `self`, `cls` and `_`
are all handled by the model rather than by a heuristic.

## Files

- `packages/pyshellforge-rude/pyproject.toml` for the manifest and the entry point
- `packages/pyshellforge-rude/src/pyshellforge_rude/` for `RULES` and the two rules
- `packages/pyshellforge-rude/tests/test_rules.py` for the suite, through `Linter.check_source`
- `docs/reference/linting.md` for the layer table and the rule codes

## Acceptance criteria

- [x] The package registers a `RULES` list through the `rude.plugins` entry
      point, and `pip install pyshellforge-rude` is the whole setup.
- [x] `PSF201` reports a module-level binding that is not `UPPER_CASE`, including
      both names of a chained assignment.
- [x] `PSF202` reports a parameter or a function-scoped binding with an upper-case
      letter, and leaves `global`, `nonlocal`, `self`, `cls` and `_` alone.
- [x] Neither rule reports in a file that mentions neither `pyshellforge` nor
      `@sh`.
- [x] Both report at warning severity.
- [x] `.coveragerc`, `[tool.mypy]` and ruff cover the second distribution from the
      repository root, and CI installs it for the coverage run and builds its
      wheel in the packaging job.
- [ ] The plugin has a release path: a tag convention, a version guard for
      `packages/pyshellforge-rude/pyproject.toml`, and a publish job that trusts a second
      PyPI project.
- [ ] A follow-up rule set for policy findings that need Python syntax only, for
      example `run()` given a single string instead of an argument list.

## Definition of done

- [x] The suite passes, and the repository gate (`ruff`, `ruff format --check`,
      `mypy`, coverage, `alint`, markdownlint) passes with the distribution in it.
- [x] `docs/reference/linting.md` is linked from `docs/README.md` and names what
      the plugin cannot see.
- [x] `CHANGELOG.md` records the distribution under `Unreleased`.
- [ ] `docs/development/releasing.md` documents the second publish path.
