---
id: decision-3
title: tox for the version matrix, Pixi for day-to-day work
date: 2026-11-09
status: Accepted
references: [tox.ini, .github/workflows/ci.yml, docs/development/testing.md]
---

## Context

CI tested Python 3.11, 3.12 and 3.13 on Linux, macOS and Windows by installing
the checkout with `pip install -e ".[dev]"` and running pytest. An editable
install is not what a user gets from PyPI, so a broken wheel or a missing
`py.typed` would have passed the matrix; the matrix also could not be reproduced
locally without juggling virtualenvs by hand.

Pixi already pins the toolchain for linting, coverage, docs and every other task.
The question was whether Pixi should also own the version matrix.

## Decision

`tox.ini` owns multi-version testing; Pixi stays the day-to-day runner.

- `env_list = py311, py312, py313, py314, lint, typecheck`
- each Python environment builds a wheel, installs it with the `dev` extra, and
  runs `pytest tests automation/tests` with coverage into `.tox/.coverage.<env>`
- `tox -e coverage` merges those files and enforces `fail_under = 90`
- CI runs one cell per OS x version and invokes `tox -e py`, which selects the
  environment matching the interpreter `setup-python` placed on `PATH`

Pixi keeps the tasks that need pinned external binaries (`ruff`, `alint`, `vale`,
`lychee`, `markdownlint-cli2`, `gh`) and the aggregate `pixi run automation check` gate.

## Consequences

- The matrix tests a built wheel with declared dependencies, which is the
  failure mode it exists to catch.
- Reproducing CI locally is one command per interpreter (`tox -e py312`) with no
  environment juggling, and `skip_missing_interpreters` keeps it usable on a
  laptop with two Pythons.
- Adding Python 3.15 is a two-line change: `env_list` plus the CI matrix.
- Two task runners exist, so documentation has to say which answers which
  question; `docs/development/testing.md` and `tooling.md` do.
- Coverage is merged per environment locally; aggregating it across CI cells
  needs artifact upload and is tracked as `task-7`.

## Alternatives considered

- **Keep the raw `pip install -e` matrix.** Rejected: it never exercises the
  built package and duplicates environment setup in YAML.
- **Use Pixi environments for every Python version.** Rejected: Pixi favors one
  locked environment per feature, and a per-version environment set multiplies
  the lock file and build time for a check tox already does well.
- **Use `uv` instead of tox.** Plausible and faster, but tox is the convention in
  the source repositories and its `env_list`/`posargs` interface reads well in
  documentation.
