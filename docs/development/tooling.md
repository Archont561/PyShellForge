# Tooling

Three layers, each with one job: Pixi owns the environment, doit owns the task
graph, and the Python modules in `automation/` own the work. Hooks, CI and the
documentation therefore run identical commands against identical tool versions.

```sh
pixi run automation list     # discover every task
pixi run automation check    # the whole gate, as one task graph
python -m automation.docs    # one module, with no task runner involved
```

`dodo.py` is the registry: it names each task, points at a `main()` or a command,
and declares the `check` graph. Automation modules never import doit, so they stay
testable and independently runnable.

## Environment

```sh
python -m automation.restore  # first run: Pixi, the environment and the hooks
pixi install --locked         # when Pixi is already present
pixi run install-hooks        # lefthook git hooks
```

The environment carries every linter `pixi run automation check` needs, including Vale and
lychee, so no task downloads a binary at run time. The distribution is installed
editable from `[pypi-dependencies]`, which points at the `packages/pyshellforge/` project
directory; there is no pip-based reinstall task, because the environment does not
ship pip.

`python -m automation.restore` is the one command that cannot sit behind the
environment, because it is what creates the environment: it downloads the official
installer (to a file, not a pipe), runs `pixi install --locked`, then
`pixi run install-hooks`, and skips the hooks with a printed reason when the
working copy is not a git checkout. `python -m automation.restore --check` reports
the state and exits non-zero when the repository is not ready. Pixi keeps both
entry points (`restore`, `install-hooks`); everything else is a doit task.

`pip install -e "packages/pyshellforge[dev]"` still works if you prefer plain pip; the
tasks below are the canonical commands.

## Tasks

`pixi run automation <task>`; `pixi run automation list` prints the same table with
each task's docstring.

| Task | Runs |
| --- | --- |
| `pixi run restore` | `python -m automation.restore` (Pixi must already exist) |
| `pixi run automation test` | `pytest -c packages/pyshellforge/pyproject.toml packages/pyshellforge/tests` |
| `pixi run automation test-automation` | `pytest -c packages/pyshellforge/pyproject.toml automation/tests` |
| `pixi run automation test-all` | Both suites |
| `pixi run automation coverage` / `coverage-all` | Coverage with `coverage.xml` |
| `pixi run automation test-matrix` | `tox -c packages/pyshellforge/tox.ini`: every installed interpreter, isolated virtualenvs |
| `pixi run automation coverage-merge` | Merge per-interpreter coverage and enforce the gate |
| `pixi run automation lint` / `format` / `format-check` | ruff |
| `pixi run automation lint-clean-code` | `python -m automation.clean_code` (rude Clean Code rules) |
| `pixi run automation typecheck` | `mypy --config-file packages/pyshellforge/pyproject.toml` (strict) |
| `pixi run automation check-docs` | `python -m automation.clean_code` | Enforce Clean Code rules on both package source trees, automation, and dodo.py |
| `python -m automation.docs` |
| `pixi run automation readme` / `readme-check` | Regenerate / verify `README.md` and `packages/pyshellforge/README.md`, banner included |
| `pixi run automation banner` | Draw text as FIGlet art (`automation.banner`); `--comment` prefixes each row for a script header |
| `pixi run automation agents` / `agents-check` | Regenerate the marked AGENTS.md sections / verify the marker contract |
| `pixi run automation lint-features` | `python -m automation.gherkin` |
| `pixi run automation lint-markdown` | markdownlint-cli2 |
| `pixi run automation lint-prose` | Vale with the Microsoft style |
| `pixi run automation lint-links` | lychee |
| `pixi run automation alint` | Repository conventions |
| `pixi run automation actionlint` | GitHub Actions workflows |
| `pixi run automation lint-commit` | convco (conventional commits), read from stdin |
| `pixi run automation build` / `check-packages` | `python -m build --outdir dist pyshellforge`, `twine check` |
| `pixi run automation check-release` / `release-build` | The tag/version guard alone / the full release build |
| `pixi run automation check` | The aggregate gate as a dependency graph: lint, format, types, Clean Code, docs, Gherkin, forms, README, AGENTS.md, alint, actionlint, markdownlint, prose, links, release guard |
| `pixi run automation -n 4 check` | The same graph, four tasks at a time |
| `pixi run automation detect-changes --base SHA --head SHA` | Classify changed files for CI |

Nothing is cached: no task declares `file_dep` or `targets`, so a task that
touches the outside world (a release upload, a document regeneration) always runs
when it is asked for. Parallelism is opt-in through doit's `-n`, because
interleaved output is hard to read in a failure.

## Repository automation

Tooling of our own is Python, in `automation/`, documented in
[`automation/README.md`](../../automation/README.md), unit-tested in
`automation/tests/` and described in Gherkin in `automation/features/`.

| Module | Purpose |
| --- | --- |
| `python -m automation.readme` | Drive readme-md-generator over `automation/readme/README.ejs` |
| `python -m automation.banner` | Draw text as FIGlet art with pyfiglet; the README banner comes from here |
| `python -m automation.docs` | Validate documentation structure, navigation, links, anchors |
| `python -m automation.gherkin` | Lint Gherkin and verify step definitions |
| `python -m automation.agents` | Maintain `AGENTS.md` through the pinned `agents-md` CLI; `--check` validates it offline |
| `python -m automation.forms` | Validate the GitHub Issue Forms in `.github/ISSUE_TEMPLATE/` |
| `python -m automation.release` | Guard the tag, build the distributions and check them |
| `python -m automation.restore` | Install Pixi, solve the environment and install the git hooks; `--check` reports state only |
| `python -m automation.detect_changes` | Choose which CI suites a change needs |

Each module keeps its own `main(argv)` and its own exit status; `dodo.py` adapts
that status into a doit failure. A module that grows too large becomes a package
(`automation/release/` already holds `build.py`), and `dodo.py` keeps pointing at
one entry point.

There is no JavaScript tooling of our own. Two npm binaries are pinned in
`package.json` and driven by Python wrappers, so the logic, the tests and the
Gherkin scenarios stay Python:

| npm binary | Wrapper | Purpose |
| --- | --- | --- |
| `readme-md-generator` | `automation.readme` | Renders `README.md` from `automation/readme/README.ejs` |
| `@eugeniughelbur/agents-md` | `automation.agents` | Creates and refreshes the generated sections of `AGENTS.md` |

## Linters, and who owns what

| Tool | Owns | Config |
| --- | --- | --- |
| ruff | Python lint and formatting | `ruff.toml` |
| rude + rude-clean-code | Clean Code structure and complexity | `packages/pyshellforge/pyproject.toml` |
| mypy | Types, strict | `packages/pyshellforge/pyproject.toml` |
| coverage.py | Coverage threshold | `.coveragerc` |
| alint | Repository structure and conventions | `.alint.yml` |
| markdownlint-cli2 | Markdown formatting | `.markdownlint-cli2.yaml` |
| Vale + Microsoft | Spelling, terminology, editorial rules | `.vale.ini`, `.vale/styles/` (vendored) |
| lychee | External links and fragments | `lychee.toml` |
| gherlint | Gherkin style | `gherlint.toml` |
| convco | Commit messages, changelog | `.versionrc` |
| automation.docs | Documentation structure and internal links | in-repo |
| automation.forms | GitHub Issue Forms schema | in-repo |

The Clean Code gate selects only the nine `CC` rules; ruff handles general
Python linting. It checks both `packages/*/src` trees, all of `automation/`, and
`dodo.py`. Function length (CC101) is limited to 60 lines because the rule
counts signatures and docstrings; every other rule uses the plugin default.
The wrapper passes the configuration explicitly and fails on warnings, which the
underlying `rude check` command alone does not. Use
`python -m automation.clean_code --json` for machine-readable findings or pass
paths to check a subset.

## Git hooks

`lefthook.yml` runs the fast checks on commit (lint, format, types, Clean Code, Gherkin,
documentation, README freshness, alint, actionlint), validates the commit message,
and runs the suites before push. Hooks call `pixi run --locked automation <task>`,
so a stale environment is detected immediately and the hook runs exactly what
`pixi run automation <task>` runs.

## Sandbox

`pixi-sandbox.toml` describes a verifiable pack of the locked environments
(`default` and `gherkin`) for `linux-64` and `osx-arm64`, published by
`.github/workflows/pixi-sandbox.yml`. Restoring it gives the same tool versions as
CI without solving dependencies again.

## Next

- [Testing](testing.md) for what those suites contain.
- [Documentation](documentation.md) for the checks that guard `docs/`.
