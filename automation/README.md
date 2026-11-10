# Repository automation

Tooling that operates on this repository. Nothing here ships in the
`pyshellforge` wheel, and the product never imports it.

The automation is one CLI. `doit` reads [`dodo.py`](../dodo.py) at the repository
root, which registers every task and the `check` dependency graph, and
`pixi.toml` exposes it as `pixi run automation <task>`:

```sh
pixi run automation list           # every task, with its docstring
pixi run automation check          # the whole gate, as one task graph
pixi run automation -n 4 check     # the same graph, four tasks at a time
python -m automation.docs          # one module, with no task runner involved
```

```text
automation/
├── features/        Gherkin scenarios describing the automation
├── gherkin/         the linter for those scenarios and their step definitions
├── tests/           unit and integration tests, plus the pytest-bdd steps
│   └── bdd/         step modules and the runner that binds them to features/
├── readme/          README.ejs, the template both READMEs are generated from
└── <module>/        one package per job: docs, forms, agents, release, restore
```

Modules here are ordinary Python: they expose `main(argv)`, return an exit
status, and know nothing about doit. That is why each one can be imported by the
tests in [`tests/`](tests/) and described in Gherkin under
[`features/`](features/). Step definitions live in
[`tests/bdd/`](tests/bdd/), next to the suite that runs them.

| Module | Run it with | Task | What it does |
| --- | --- | --- | --- |
| `automation.restore` | `python -m automation.restore` | `pixi run restore` | Installs Pixi when it is missing, solves the environment with `pixi install --locked` and installs the Lefthook hooks; `--check` reports state and changes nothing |
| `automation.readme` | `python -m automation.readme` | `pixi run automation readme` | Regenerates `README.md` and `packages/pyshellforge/README.md` (the PyPI long description, with its links rebased) with readme-md-generator (npm) from `automation/readme/README.ejs`; `--check` fails when either file is stale |
| `automation.agents` | `python -m automation.agents --check` | `pixi run automation agents-check` | Validates the `agents-md` marker contract in `AGENTS.md`; `--bootstrap` creates the skeleton with the pinned npm CLI |
| `automation.docs` | `python -m automation.docs` | `pixi run automation check-docs` | Validates `docs/`: required sections, navigation index, relative links, anchors, fenced-code languages, heading structure |
| `automation.gherkin` | `python -m automation.gherkin` | `pixi run automation lint-features` | Lints Gherkin files and verifies that every step has a `pytest-bdd` definition and every definition is used |
| `automation.forms` | `python -m automation.forms` | `pixi run automation check-forms` | Validates the GitHub Issue Forms in `.github/ISSUE_TEMPLATE/` against GitHub's schema; rendering them needs `gh form preview` |
| `automation.release` | `python -m automation.release` | `pixi run automation release-build` | Builds the release distributions after checking the tag against `[project].version`; `--check` runs the guard only |
| `automation.detect_changes` | `python -m automation.detect_changes` | `pixi run automation detect-changes` | Classifies changed files so CI can skip irrelevant suites |

## Conventions

- **Python only.** No JavaScript tooling of our own. Two npm binaries are pinned
  in `package.json` and driven by Python wrappers: `readme-md-generator`
  (`automation.readme`) and `@eugeniughelbur/agents-md` (`automation.agents`).
- **Testable core, thin CLI.** Logic lives in importable functions that take
  paths and injected callables; `main()` only parses arguments. This keeps the
  modules at high coverage without network or shell access.
- **No work at import time.** `dodo.py` imports these modules to discover tasks,
  so importing one must never run the automation.
- **Stable diagnostic codes.** Findings use prefixed codes (`PSF-DOC-###`,
  `PSF-FEAT-###`, `PSF-FORM-###`, `PSF-AGENT-###`) so they can be quoted in
  documentation and tests.
- **Non-zero exit on findings.** Every module exits `1` when it finds something
  and `0` otherwise; `dodo.py` turns a non-zero status into a doit failure, which
  is what CI and the git hooks rely on.
- **No caching.** No task declares `file_dep` or `targets`. A task that touches
  the outside world always runs when it is asked for, so no release upload is
  ever skipped because a file looked fresh.
- **`automation.restore` runs first.** It is the only command that does not
  assume Pixi exists, so it is plain `python -m automation.restore` rather than a
  task.

## Adding a module

1. Create `automation/<name>/` with `__init__.py`, `__main__.py` and the module
   holding the logic.
2. Re-export the public surface from `__init__.py` and keep `main(argv)` thin.
3. Add unit tests in `automation/tests/test_<name>.py` and, for user-visible
   behaviour, a scenario in `automation/features/` plus its steps in
   `automation/tests/bdd/`.
4. Register a `task_<name>()` in `dodo.py` with a docstring and a kebab-case
   `basename`, and, if the module is a gate, add that task to `GATES` so
   `pixi run automation check` runs it.
5. Add a row in the table above; if CI should run it, add a step to
   `.github/workflows/ci.yml`.
