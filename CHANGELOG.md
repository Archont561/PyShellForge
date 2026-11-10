# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- **Repository automation is one CLI.** `scripts/` became `automation/`, and every
  repository task is now registered in `dodo.py` and run through
  `pixi run automation <task>`. Pixi keeps the environment and three entry points
  (`automation`, `restore`, `install-hooks`); the twenty-odd per-script Pixi tasks
  are gone. `pixi run automation list` prints every task with its docstring,
  `pixi run automation check` is a real doit dependency graph over the fourteen
  gates, and `-n 4` runs the independent ones in parallel. Hooks, CI and the
  documentation call the same `automation` tasks, so nothing runs a command the
  registry does not know about.
- **The modules are ordinary Python.** `automation.*` keeps one `main(argv)` per
  module and never imports doit, so `python -m automation.docs` still works
  without the task runner; `dodo.py` adapts an exit status into a doit failure.
  No task declares `file_dep` or `targets`: a release upload or a regeneration
  must never be skipped because a file looked fresh.
- **The registry is checked like code.** Task names are kebab-case (set through
  `basename`, because doit derives a name from its `task_` function), `check`'s
  dependency list must match `GATES`, and `automation/features/automation_cli
  .feature` plus `automation/tests/test_dodo.py` pin both. `dodo.py` is inside the
  coverage gate (100%) and alint requires it to exist.
- **Scenarios and step definitions moved beside the automation.** The Gherkin
  suite left the distribution: `pyshellforge/features/tooling/*.feature` became
  `automation/features/*.feature`, the step modules and the pytest-bdd runner
  became `automation/tests/bdd/`, and `pyshellforge/conftest.py` is gone with the
  `pytest_plugins` registration it existed for. `pyshellforge/` now holds only the
  product: its package, `VERSION` tests and the README integration test.
- **`automation.features` became `automation.gherkin`.** The linter could not keep
  the name of the directory the scenarios now live in. It still runs as
  `pixi run automation lint-features` and now lints every tree with scenarios and
  every tree with steps (`automation/…` and `pyshellforge/…`), tolerating the ones
  that do not exist yet, so a product scenario cannot be added without being
  checked.
- **CI's change detection follows the rename.** `automation.detect_changes` emits
  `run_automation` instead of `run_scripts` and treats `automation/` as the
  automation suite; the workflow job is `Automation suite`.

- **The distribution has its own directory.** `pyshellforge/` now holds the whole
  project: `src/pyshellforge/`, `tests/`, `features/`, `tox.ini`, the manifest and
  the README PyPI shows. The repository root keeps what is repository-scoped:
  `docs/`, `scripts/`, `backlog/`, the Pixi environment and CI.
  `pyproject.toml` moved to `pyshellforge/pyproject.toml` and is the only manifest,
  so pytest, mypy and tox are pointed at it explicitly
  (`pytest -c pyshellforge/pyproject.toml`, `mypy --config-file ...`,
  `tox -c pyshellforge/tox.ini`); `pixi run` tasks carry those paths, so the
  commands contributors type did not change.
- **A second generated README.** Hatchling refuses a README outside the project
  directory, so `python -m scripts.readme` now writes `README.md` at the root and
  `pyshellforge/README.md`, the long description the package metadata points at.
  Both come from `scripts/readme/README.ejs`; the nested copy has its relative
  links rebased (`docs/` becomes `../docs/`), and `readme-check` fails if either
  file is stale.
- **`tests/conftest.py` became `pyshellforge/conftest.py`.** pytest only accepts
  `pytest_plugins` in a conftest at the rootdir, and the rootdir is now the project
  directory. The step-module list is unchanged.
- **`tox.ini` moved into the project directory**, because tox builds the package it
  finds beside its configuration. The per-environment coverage data still uses the
  repository `.coveragerc` through `COVERAGE_RCFILE`.
- **Repository tooling follows the new paths**: `scripts.release` builds
  `pyshellforge/` and reads the version from its manifest, `scripts.features` lints
  `pyshellforge/features/` against `pyshellforge/tests/bdd/`, `scripts.readme`
  writes both READMEs, and `scripts.detect_changes` treats
  `pyshellforge/features/` as documentation scope. alint gained rules for the
  package source and the package README, and the workflows, `.coveragerc`,
  `ruff.toml`, `.vale.ini`, `gherlint.toml` and `codecov.yml` moved with them.

### Added

- **Trusted publishing on a tag.** `.github/workflows/release.yml` publishes to
  PyPI when a `v*` tag is pushed: a `build` job runs `python -m scripts.release`,
  which compares the tag with `[project].version`, empties `dist/`, builds the sdist
  and the wheel and checks both with `twine check`, then a separate `publish` job in
  the `pypi` environment hands the artifact to `pypa/gh-action-pypi-publish` with
  only `id-token: write`. No API token is stored; the tag guard fails before
  anything is built, so a mismatch never reaches the upload.
- **`scripts.release`** (`pixi run release-build`, and `pixi run check-release` for
  the guard alone) as the Python counterpart of the sibling repository's
  `scripts/build-release.sh`, matching this repository's Python-only tooling rule.
  It is covered by `scripts/tests/test_release.py` and by
  `features/tooling/release_build.feature`.
- **`docs/development/releasing.md`**: the workflow, the manual steps (version bump,
  tag), the local dry run, and what stays manual. `alint` gained rules requiring the
  workflow and the script to exist.

### Changed

- **The package is a skeleton again.** `src/pyshellforge/__init__.py` is the whole
  package and it exposes one attribute: `VERSION`, read from `[project].version`
  in `pyproject.toml` when a checkout is present, then from installed distribution
  metadata, then from a constant, so an import never raises. The version keeps its
  single source of truth; the fallbacks exist because a wheel does not ship
  `pyproject.toml`. `tests/unit/test_version.py` pins that order and the shapes of
  manifest that must be rejected.

### Removed

- **Everything the package used to implement**: `core/`, `ast/`, `renderers/`,
  `backends/`, `validation/`, `cli/` and `utils/` (35 modules), `_version.py`, the
  `src/__init__.py` version shim and the `psf` console script. The
  `[project.scripts]` entry and the wheel-content assertions in CI are updated with
  them, so `python -m build` still produces a wheel that passes its own check.
- **The tests and the documentation that described them**: the twelve unit modules
  for nodes, quoting, validation and rendering, both integration modules for shell
  syntax and the CLI, the product Gherkin feature and its steps, `tests/support.py`,
  the `guides/`, `concepts/`, `reference/` and `architecture/` documentation
  sections, and the `examples/` definitions with their snapshots.
  `tests/integration/test_readme.py` and `docs/development/` remain, and the docs
  validator now requires the single section that has pages.
- **The README sections that promised a library.** The generated file states what
  exists—one attribute, one module—lists the repository layout and the roadmap, and
  points at `backlog/` for the work that has not happened. A test fails if the
  README mentions `psf render`, `psf validate` or `ShellScript` again before the
  code backs it.

### Added

- **GitHub Issue Forms, validated offline.** `bug_report.yml` and
  `feature_request.yml` ask for the version, the interpreter, the affected area and
  a minimal reproduction; `config.yml` adds the contact links and disables blank
  issues. `python -m scripts.forms` implements the schema check (codes
  `PSF-FORM-001` to `PSF-FORM-017`) in `pixi run check`, the pre-commit hook and
  the CI policy job; rendering a form is the manual `gh form preview` step.

- **`scripts.restore`**: one command that takes a fresh checkout or a short-lived
  sandbox to a working repository. It finds Pixi on `PATH` or in `~/.pixi/bin`,
  installs it from the official installer when it is missing, repairs a binary that
  lost its executable bit, solves the environment with `pixi install --locked`, and
  installs the Lefthook hooks when the working copy is a git checkout. `--check`
  reports state, `--relock` re-solves first, and hooks are skipped with a printed
  reason outside a checkout. Covered by `scripts/tests/test_restore.py` and
  `features/tooling/session_restore.feature`.

### Fixed

- **`pixi run check-packages` rejected the wheel it had just built.** hatchling
  writes `Metadata-Version: 2.5`, which twine 6.2 cannot parse; the pin is now
  `twine>=7,<8`, and `python -m build` plus `twine check` pass on the skeleton
  wheel.
- **`pixi run test-all` and `coverage-all` failed with `No module named pip`.** The
  conda environment ships no pip, so the `install-projects` task could never work;
  the package comes from `[pypi-dependencies]` and the task is gone.
- **A Gherkin step leaked a monkeypatch into other tests.** `steps_restore.py`
  assigned to `generate.install_pixi`, which persisted for the rest of the session
  and failed only in a full-suite run; `restore()` now takes an injectable
  installer.
- **Prose and link linting needed binaries a contributor had installed by hand.**
  `vale` and `lychee` are conda-forge dependencies and part of `pixi run check`.

### Planned

- Core engine: AST base, `ShellScript`, Bash renderer, comments, variables, commands
- Functions, expressions, conditions, loops and arrays
- Pipes, redirects, heredocs, subshells and command substitution
- Validation, diagnostics, a CLI, and `bash -n` in CI
- Custom renderers and the POSIX backend

## [0.1.0]—2026-11-09

First public release. The engine, the shell subset, validation, the CLI,
examples, documentation and CI are all in place.

### Added

**Core**

- `ShellScript` container with `add`, `extend`, `insert`, `clear`, container
  protocol, `render()`, `write(executable=)`, `validate()`, `tree()`, `to_dict()`.
- `Node` base class with generic child discovery, `walk()`, `to_dict()` and a
  box-drawing `tree()` dump.
- `RenderContext` (immutable indentation/shell/strict state).
- `NodeRegistry` plus `register_node_type()` for plugin discovery.
- Exception hierarchy: `PyShellForgeError`, `RenderError`,
  `UnsupportedNodeError`, `ValidationError`, `IdentifierError`,
  `ScriptLoadError`, `BackendError`.

**AST**

- Commands: `Command`, `Echo`, `Printf`, `Exec`, `Exit`, `Return`, `Source`,
  `Comment`.
- Variables: `Variable`, `Export`, `Local`, `Readonly`, `Unset`, `VariableRef`,
  `Array`.
- Functions: `Function` (with `params` bindings and `description`), `Call`,
  `Argument`.
- Control flow: `If`, `Elif`, `Else`, `For`, `While`, `Until`, `Case`,
  `CaseBranch`, `Break`, `Continue`.
- Composition: `Pipe`, `And`, `Or`, `Subshell`, `CommandGroup`,
  `CommandSubstitution`.
- Redirects: `Redirect`, `Append`, `HereDoc` (quoted or expanding delimiters,
  `<<-` support), `Stream` constants.
- Words: `Literal`, `RawShell`, `CommandArg`, `Concat`; `pathlib.Path` accepted
  wherever a word is.
- Conditions: `Equals`, `NotEquals`, `GreaterThan`, `LessThan`, `Matches`,
  `FileExists`, `DirectoryExists`, `IsExecutable`, `AndCondition`,
  `OrCondition`, `NotCondition`, plus `combine_and`/`combine_or`/`negate`.

**Renderer**

- `BaseRenderer` with MRO-aware dispatch (method naming convention, explicit
  `register()`, and `@register_renderer` free functions).
- `BashRenderer` reference implementation for every node.
- Documented quoting strategy: bare word → double quotes → single quotes →
  escaped double quotes, with assignment values and test operands always quoted.
- Documented blank-line policy: `simple` statements adjacent, `compound` and
  `comment` separated.
- Relative indentation levels; heredoc bodies and multi-line words are
  protected from re-indentation.
- Empty blocks render as `:` so generated Bash is always syntactically valid.

**Backends**

- `BashBackend` (`#!/usr/bin/env bash`, `set -euo pipefail`).
- `PosixBackend` / `PosixRenderer` (`#!/bin/sh`, `set -eu`, `[ ... ]` tests,
  `.` instead of `source`, `UnsupportedNodeError` for arrays and `=~`).
- `get_backend()` / `available_backends()`.

**Validation**

- `Validator` with context tracking (`in_function`, `in_loop`, `in_case`,
  duplicate function names) and field-based locations
  (`script[3].body[0].then[1]`).
- 40 stable diagnostic codes across structure (PSF1xx), names (PSF2xx),
  context (PSF3xx) and safety (PSF4xx).
- `Diagnostic`, `DiagnosticBag`, `Severity`, `@rule` registration.

**CLI**

- `psf render` (`-o`, `--stdout`, `--shell`, `--strict/--no-strict`,
  `--indent`, `-x`, `--no-validate`).
- `psf validate` (`--json`, `--strict`, `--color`).
- `psf inspect` (`--json`).
- `psf version`, `psf --version`, `python -m pyshellforge`.
- Script discovery: `script` attribute, unique instance, or `build()`.

**Versioning**

- `pyshellforge.__version__` is read from `pyproject.toml` via
  `pyshellforge._version` (distribution metadata → source-tree `pyproject.toml`
  → fallback constant), so the version has exactly one source of truth.
- `src/__init__.py` is a shim that exposes the same value for tooling; it is
  excluded from the published wheel.
- `tests/unit/test_version.py` pins package, shim, CLI and packaging metadata
  together.

**Examples & docs**

- Five complete examples: `hello_world`, `deployment`, `backup`,
  `docker_build`, `system_setup`.
- Documentation: getting started, API reference, AST design, renderers,
  examples, contributing.

**Testing & CI**

- 650 tests: per-node unit tests, quoting/escaping tests, validation tests,
  plugin tests, golden-file snapshots, `bash -n` checks, `shellcheck -S error`
  checks, execution-semantics tests, quoting round-trips through a real shell,
  and CLI tests.
- GitHub Actions: tests on Linux and macOS across Python 3.11–3.13, plus a lint
  and typing workflow.
- `tox.ini` with matching environments.

### Notes

- `PyShellForge` is a working name; PyPI and GitHub availability should be
  confirmed before an official release.
- Rendering never executes generated scripts. Shell execution is out of scope.
- Arithmetic (`$(( ))`) and other constructs the AST does not model are
  available through the explicit `RawShell` escape hatch.

[Unreleased]: https://github.com/Archont561/PyShellForge/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Archont561/PyShellForge/releases/tag/v0.1.0
