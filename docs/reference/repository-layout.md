# Repository layout

```text
packages/              importable distributions, one project directory each
  pyshellforge/        the distribution: package, tests and manifest
    src/               the typed package: AST, core, renderers and version
    tests/             unit and integration tests for the distribution
    pyproject.toml     metadata, build targets, pytest and mypy configuration
    tox.ini            the multi-interpreter matrix
  pyshellforge-rude/   the Rude plugin: rules, tests and manifest
    src/               the plugin package, which exposes the RULES list
dodo.py                the task registry behind `pixi run automation`
automation/            repository automation: one module per job, plus tests and features
automation/features/   Gherkin scenarios describing the automation
automation/tests/      unit, integration and pytest-bdd tests for the automation
docs/                  documentation: concepts, guides, reference and development
backlog/               tasks, milestones and decisions (Backlog.md)
pixi.toml              developer environment and task runner
```

Both distributions are project directories under `packages/`, so everything
that builds or tests them runs from the root with an explicit path
(`pixi run automation build`, `pixi run automation test-all`).
`packages/pyshellforge/README.md` is a copy of the landing page with its relative links
rebased, because PyPI needs a long description inside the project directory.

Repository automation is one CLI. `doit` reads `dodo.py`, which registers every
task and the `check` dependency graph; the modules under `automation/` stay
ordinary Python and can also be run directly (`python -m automation.docs`). The
task catalogue is [Tooling](../development/tooling.md).

Back to the [documentation index](../README.md).
