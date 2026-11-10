<!--
  Generated file - do not edit README.md by hand.

  Source template : automation/readme/README.ejs
  Generator       : readme-md-generator (pinned in package.json)
  Regenerate with : pixi run automation readme   (python -m automation.readme)
  Verify in CI    : pixi run automation readme-check
-->

<h1 align="center">PyShellForge</h1>
<p align="center"><em>Write shell scripts in Python. Render clean Bash.</em></p>
<p align="center">
  <img alt="Version: 0.1.0" src="https://img.shields.io/badge/version-0.1.0-blue.svg?cacheSeconds=2592000" />
  <img alt="python >=3.11" src="https://img.shields.io/badge/python-%3E%3D3.11-blue.svg" />
  <a href="https://github.com/Archont561/PyShellForge/blob/master/LICENSE" target="_blank">
    <img alt="License: MIT" src="https://img.shields.io/github/license/Archont561/pyshellforge" />
  </a>
  <a href="https://github.com/Archont561/PyShellForge/actions" target="_blank">
    <img alt="Tests" src="https://img.shields.io/badge/tests-passing-brightgreen.svg" />
  </a>
  <a href="https://github.com/Archont561/PyShellForge" target="_blank">
    <img alt="Typing: mypy strict" src="https://img.shields.io/badge/typing-mypy%20strict-blue.svg" />
  </a>
  <a href="https://codecov.io/gh/Archont561/pyshellforge" target="_blank">
    <img alt="Coverage" src="https://img.shields.io/codecov/c/github/Archont561/pyshellforge.svg" />
  </a>
  <a href="https://github.com/Archont561/PyShellForge/tree/main/docs" target="_blank">
    <img alt="Docs validated" src="https://img.shields.io/badge/docs-validated-informational.svg" />
  </a>
</p>

```text
    ____        ____  __         __  ______
   / __ \__  __/ __/ / /_  ___  / / / ____/___  _____________ ____
  / /_/ / / / / /_  / _ \/ _ \/ / / /_  / __ \/ ___/ ___/ _ `/ _ \
 / ____/ /_/ / __/ /  __/  __/ / / __/ / /_/ / /  / /__/ /_/ /  __/
/_/    \__, /_/   /_/\___/\___/_/_/   /_/\____/_/   \___/\__, /\___/
      /____/                       Write Python.         /____/
                                    Render Bash.
```

> A Python-native DSL for building, composing and rendering structured Bash scripts.

### 🏠 [Homepage](https://github.com/Archont561/PyShellForge#readme)

## Table of contents

- [What it is](#what-it-is)
- [Prerequisites](#prerequisites)
- [Install](#install)
- [Usage](#usage)
- [Repository layout](#repository-layout)
- [Run tests](#run-tests)
- [Roadmap](#roadmap)
- [Author](#author)
- [🤝 Contributing](#-contributing)
- [Show your support](#show-your-support)
- [📝 License](#-license)

## What it is

PyShellForge aims to be a Python-native DSL that builds structured Bash: you
describe the script as objects and the library renders shell text you can review.

**What exists today is the skeleton.** The package ships one module,
`pyshellforge/src/pyshellforge/__init__.py`, and it exposes one attribute:

```python
>>> import pyshellforge
>>> pyshellforge.VERSION
'0.1.0'
```

`VERSION` is read from `[project].version` in `pyproject.toml` when the package
runs from a source checkout, falls back to installed distribution metadata, and
last to a constant, so an import never fails. There is no renderer, no AST and no
CLI yet, and nothing in this README describes one. The work that would change
that is tracked in [`backlog/`](../backlog/) and [`CHANGELOG.md`](../CHANGELOG.md).

Repository conventions, the backlog workflow and the documentation policy are in
[`AGENTS.md`](../AGENTS.md) and [`docs/development/`](../docs/development/).

## Prerequisites

- python: `>=3.11`

## Install

```sh
pip install pyshellforge
```

For development, use the locked environment; it is what the hooks and CI use:

```sh
command -v pixi || python -m automation.restore   # installs Pixi, solves the env
pixi run install-hooks                           # Lefthook git hooks
```

`pip install -e "pyshellforge[dev]"` works too for contributors who do not want
Pixi.

## Usage

```sh
python -c "import pyshellforge; print(pyshellforge.VERSION)"
```

## Repository layout

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
docs/                         documentation and the development guides
backlog/                      tasks, milestones and decisions (Backlog.md)
pixi.toml                     developer environment and task runner
```

The distribution is a project directory inside the repository, so everything
that builds or tests it runs from the root with an explicit path
(`pixi run automation build`, `pixi run automation test-all`);
`pyshellforge/README.md` is a copy of this page with its relative links rebased,
because PyPI needs a long description inside the project directory.

Repository automation is one CLI. `doit` reads `dodo.py`, which registers every
task and the `check` dependency graph; the modules under `automation/` stay
ordinary Python and can also be run directly (`python -m automation.docs`).

## Run tests

```sh
pixi run automation test-all
```

The whole gate is one task; the individual checks are tasks too, and
`pixi run automation list` prints them all:

```sh
pixi run automation check              # every check below, in one graph
pixi run automation -n 4 check         # the same, four at a time

pixi run automation lint               # ruff
pixi run automation format-check
pixi run automation typecheck          # mypy, strict
pixi run automation lint-features      # Gherkin + step definitions
pixi run automation check-forms        # GitHub Issue Forms schema
pixi run automation check-docs         # docs structure, links, anchors
pixi run automation lint-markdown      # markdownlint-cli2
pixi run automation lint-prose         # Vale
pixi run automation lint-links         # lychee
pixi run automation coverage-all       # tests with a coverage gate
pixi run automation test-matrix        # tox: every installed Python, each in its own venv
pixi run automation agents-check       # AGENTS.md keeps the agents-md marker contract
```

`pyshellforge/tests/` covers the distribution, `automation/tests/` covers the
repository automation, and the Gherkin scenarios in `automation/features/` bind
to `pytest-bdd` so `pixi run automation lint-features` fails on a step with no
definition. Tests and scenarios sit beside the code they describe: a module in
`automation/` is covered by `automation/tests/` and, when it has user-visible
behaviour, by a scenario in `automation/features/`.

`tox` answers a different question: it builds a wheel, installs it with the `dev`
extra on Python 3.11 through 3.14, and runs the suite, so a packaging mistake
fails the matrix instead of passing it. CI runs one `tox -e py` per OS and
version cell.

## Roadmap

| Phase | Scope | State |
| --- | --- | --- |
| 0 | Skeleton: one module, `VERSION` read from `pyshellforge/pyproject.toml` | ✅ |
| 1 | Core engine: AST base, `ShellScript`, Bash renderer, comments, variables, commands | ⏳ planned |
| 2 | Functions, expressions, conditions, loops, arrays | ⏳ planned |
| 3 | Pipes, redirects, heredocs, subshells, command substitution | ⏳ planned |
| 4 | Validation, diagnostics, CLI, `bash -n` in CI | ⏳ planned |
| 5 | Documentation, packaging, custom renderers | ⏳ planned |

See [CHANGELOG.md](../CHANGELOG.md) for the state of `v0.1.0`.

## Author

👤 **PyShellForge contributors**

- GitHub: [@Archont561](https://github.com/Archont561)

## 🤝 Contributing

Contributions, issues and feature requests are welcome!<br />Feel free to check the [issues page](https://github.com/Archont561/PyShellForge/issues). You can also take a look at the [contributing guide](https://github.com/Archont561/PyShellForge/blob/master/CONTRIBUTING.md).

```sh
git clone https://github.com/Archont561/PyShellForge
cd pyshellforge
command -v pixi || python -m automation.restore   # installs Pixi, solves the env
pixi run install-hooks                           # Lefthook git hooks
pixi run automation test-all
```

Both `README.md` and `pyshellforge/README.md` are generated: edit
`automation/readme/README.ejs`, never the output.
`AGENTS.md` follows the same rule: its marked sections are maintained by the
pinned [`agents-md`](https://github.com/eugeniughelbur/agents-md) CLI, and
`pixi run automation agents-check` fails when a marker or a section goes missing.

```sh
pixi run automation readme          # rewrite both READMEs (readme-md-generator, npm)
pixi run automation readme-check    # fail if either README is stale (run by CI)
```

## Show your support

Give a ⭐️ if this project helped you!

## 📝 License

Copyright © 2026 [PyShellForge contributors](https://github.com/Archont561).<br />
This project is [MIT](https://github.com/Archont561/PyShellForge/blob/master/LICENSE) licensed.

***

*This README was generated with ❤️ by [readme-md-generator](https://github.com/kefranabg/readme-md-generator) from [`automation/readme/README.ejs`](../automation/readme/README.ejs).*
