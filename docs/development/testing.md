# Testing

```sh
pixi run automation test-all        # product suite + automation suite
pixi run automation coverage-all    # the same run with the coverage gate
```

The distribution is the `pyshellforge/` project directory, so both tasks point
pytest at its configuration file and then name the suites explicitly:

```sh
python -m pytest -c pyshellforge/pyproject.toml pyshellforge/tests automation/tests
```

Run from inside `pyshellforge/`, a bare `pytest` finds the same configuration and
collects the product suite only.

## Layout

| Path | Contents |
| --- | --- |
| `pyshellforge/tests/unit/` | `test_version.py`: `VERSION` and the order it is resolved in |
| `pyshellforge/tests/integration/` | `test_readme.py`: the generated READMEs, their links and their metadata |
| `automation/tests/` | Unit and integration tests for the modules in `automation/` |
| `automation/tests/bdd/` | Step definitions binding `automation/features/**/*.feature` with pytest-bdd |
| `automation/tests/bdd/conftest.py` | Registers the step modules; `pytest_plugins` is only accepted at the pytest rootdir, which this suite sits outside |

Product tests live with the product; automation tests live with the automation.
The two suites are never mixed: `pixi run automation test` and
`pixi run automation test-automation` run one each, and `test-all` runs both.
The automation suite carries its own Gherkin scenarios in
`automation/features/`, so a change to a module and the scenario that describes
it are always in the same tree.

The product suite is small because the package is: one module, one attribute.
`test_version.py` covers the three resolution steps (a `pyshellforge/pyproject.toml`
found by walking up from the module, installed distribution metadata, the fallback
constant) and the shapes of a manifest that must be rejected, so
`import pyshellforge` is proven not to raise in a wheel, a checkout or a vendored
copy.

## Gherkin scenarios

User-visible behaviour of the repository automation is described in
`automation/features/`, one file per module:

```text
automation/features/
├── agents_file.feature         AGENTS.md maintenance
├── automation_cli.feature      the dodo.py task registry
├── docs_validation.feature     documentation structure and links
├── feature_lint.feature        Gherkin linting
├── issue_forms.feature         GitHub Issue Forms
├── readme_generation.feature   README generation
├── release_build.feature       the tag guard and the release build
└── session_restore.feature     environment restore and git hooks
```

```sh
pixi run automation lint-features    # undefined steps, unused definitions, wrong step order
pixi run automation test-all         # pytest-bdd executes the scenarios
```

A new behaviour starts with a scenario and a failing test. `automation.gherkin`
reports `PSF-FEAT-006` for a step with no definition and `PSF-FEAT-007` for a
definition no scenario uses, so the two sides cannot drift. The product has no
feature file because it has no rendering behaviour to describe yet; the first one
lands with the first node.

## Coverage

```sh
pixi run automation coverage        # terminal report plus coverage.xml
pixi run automation coverage-all    # what CI runs
```

`.coveragerc` sets `source = pyshellforge, automation` and `fail_under = 90`, so the
gate covers the package (resolved through the installed distribution, which the
Pixi environment installs from `pyshellforge/`) and the repository tooling in one
number. Codecov reports
the same run; it does not fail the build, because the threshold belongs to
coverage.py.

`pyshellforge/tests/`, `pyshellforge/conftest.py` and `automation/tests/` are omitted
from the report: they are test code, and counting them would let a low-coverage
assertion hide behind a high-coverage suite.

## Multiple Python versions

`tox` answers the question Pixi cannot: does the package build and pass on each
interpreter a user might have?

```sh
pixi run automation test-matrix       # every interpreter installed locally
pixi run automation test-matrix-one   # the matching interpreter only
pixi run automation coverage-merge    # merge the per-interpreter coverage data
tox -c pyshellforge/tox.ini -e lint,typecheck   # the non-test environments
```

Every environment builds a wheel and installs it with the `dev` extra in a fresh
virtualenv, so a packaging mistake fails the matrix instead of passing it. CI runs
one `tox -e py` per operating system and version cell, and `tox -e coverage` merges
the per-interpreter data into one report.
