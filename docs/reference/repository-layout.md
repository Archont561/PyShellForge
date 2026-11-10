# Repository layout

```text
pyshellforge/                 the distribution: package, tests and manifest
pyshellforge/src/             the package: __init__.py exposes VERSION, plus py.typed
pyshellforge/tests/           unit and integration tests for the distribution
pyshellforge/pyproject.toml   metadata, build targets, pytest and mypy configuration
pyshellforge/tox.ini          the multi-interpreter matrix
dodo.py                       the task registry behind `pixi run automation`
automation/                   repository automation: one module per job, plus tests and features
automation/features/          Gherkin scenarios describing the automation
automation/tests/             unit, integration and pytest-bdd tests for the automation
docs/                         documentation: concepts, guides, reference and development
backlog/                      tasks, milestones and decisions (Backlog.md)
pixi.toml                     developer environment and task runner
```

The distribution is a project directory inside the repository, so everything
that builds or tests it runs from the root with an explicit path
(`pixi run automation build`, `pixi run automation test-all`).
`pyshellforge/README.md` is a copy of the landing page with its relative links
rebased, because PyPI needs a long description inside the project directory.

Repository automation is one CLI. `doit` reads `dodo.py`, which registers every
task and the `check` dependency graph; the modules under `automation/` stay
ordinary Python and can also be run directly (`python -m automation.docs`). The
task catalogue is [Tooling](../development/tooling.md).

Back to the [documentation index](../README.md).
