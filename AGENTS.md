# AGENTS.md

> Guidance for AI agents (and humans) working in this repository. Read this first.
> **Before changing anything, verify live state**: read the code, the manifests and
> the gates instead of trusting a summary. Do not act on stale assumptions.

<!-- agents-md:begin id=overview -->
## Overview

PyShellForge aims to be a Python-native DSL that builds structured Bash. **What
exists today is the skeleton**: the distribution lives in `pyshellforge/`, the
package is a single module, `pyshellforge/src/pyshellforge/__init__.py`, and it
exposes one attribute, `VERSION`, read from `[project].version` in
`pyshellforge/pyproject.toml` with fallbacks to installed distribution metadata and
then a constant. There is no renderer, no AST, no validator and no
CLI, so nothing in the repository may claim otherwise.

The repository around that module is complete and is the part worth reading:
locked Pixi environment, tox matrix, a Gherkin-checked task registry (`dodo.py`)
that validates the docs, the README, `AGENTS.md` and the GitHub Issue Forms, and
documentation checked like code. The license is MIT, the floor is
Python 3.11, and the library roadmap lives in `backlog/`.
<!-- agents-md:end id=overview -->

<!-- agents-md:begin id=commands -->
## Commands

- Environment: `command -v pixi || python -m automation.restore`, then
  `pixi run install-hooks`.
- Discover the automation: `pixi run automation list`. Every other command in this
  file is `pixi run automation <task>`; the tasks live in `dodo.py`.
- Test: `pixi run automation test-all`, which is
  `python -m pytest -c pyshellforge/pyproject.toml pyshellforge/tests automation/tests`
  (the distribution is a project directory, so pytest gets its configuration
  explicitly). One suite at a time: `test` and `test-automation`. Every installed
  interpreter in its own virtualenv: `pixi run automation test-matrix`
  (`tox -c pyshellforge/tox.ini`).
- Coverage (what CI gates on): `pixi run automation coverage-all`; merge the tox
  matrix with `pixi run automation coverage-merge`.
- Lint, format, types: `pixi run automation lint`, `format-check`, `typecheck`.
- Documentation: `check-docs`, `lint-markdown`, `lint-prose`, `lint-links`.
- Conventions and workflows: `alint`, `actionlint`, `lint-features`, `check-forms`.
- Release: `check-release` (tag/version guard) and `release-build` (guard, build,
  `twine check`); publishing happens in CI on a `v*` tag.
- Generated files: `readme` and `agents`, plus their `-check` counterparts.
- Everything at once: `pixi run automation check`, or
  `pixi run automation -n 4 check` to run the independent gates in parallel.
<!-- agents-md:end id=commands -->

<!-- agents-md:begin id=testing -->
## Testing

Two halves and one gate. `pyshellforge/tests/` covers the product and the README:
`pyshellforge/tests/unit/test_version.py` proves `VERSION` and the order it
resolves in (the manifest, then installed metadata, then the constant), and
`pyshellforge/tests/integration/test_readme.py` proves the generated README and its
`pyshellforge/README.md` copy keep their sections, their links and their metadata
in step with the manifest and `package.json`. `automation/tests/` covers the
repository tooling. Gherkin scenarios in `automation/features/` bind the tooling
to `pytest-bdd`, and `pixi run automation lint-features` fails on a step with no definition or
a definition no scenario uses.

A change is done when `pixi run automation check` passes: ruff, format, mypy, the
documentation checks, Gherkin, issue forms, README freshness, the `AGENTS.md`
marker contract, alint, markdownlint, Vale and lychee. Test suites and the 90
percent coverage gate are `pixi run automation test-all` and `pixi run automation coverage-all`. The
product suite is deliberately small; when behaviour returns, its tests return with
it, first as a Gherkin scenario, then as a unit test, then as an execution test
when only a real process can prove the behaviour.
<!-- agents-md:end id=testing -->

<!-- agents-md:begin id=structure -->
## Project structure

| Path | Contents |
| --- | --- |
| `pyshellforge/` | The distribution: manifest, package, tests, `tox.ini`, its README |
| `pyshellforge/src/pyshellforge/` | The package: `__init__.py` exposes `VERSION`, plus `py.typed` |
| `pyshellforge/tests/` | Product and README tests for the distribution |
| `automation/` | Repository automation, with its tests in `automation/tests/` |
| `automation/features/` | Gherkin scenarios describing the automation |
| `automation/gherkin/` | The linter for those scenarios and their step definitions |
| `docs/` | Documentation: `docs/README.md` indexes `docs/development/` |
| `backlog/` | Tasks, milestones and decision records for the library |
| `.github/ISSUE_TEMPLATE/` | Bug report and feature request forms, plus `config.yml` |

The important code is `pyshellforge/src/pyshellforge/__init__.py` and, for the
repository itself, `automation/restore/`, `automation/docs/`, `automation/release/` and
`automation/forms/`. The backlog is
the source of truth for what the library will become.
<!-- agents-md:end id=structure -->

<!-- agents-md:begin id=conventions -->
## Code style & conventions

- Ruff for lint and format (line length 100), mypy strict, `from __future__ import
  annotations` in every module, full type annotations and docstrings that explain
  why the code exists.
- **Nothing that is not implemented.** No page, README section, issue form field or
  docstring may describe behaviour the package cannot back. When code is removed,
  its prose and its tests go in the same change.
- **One source of truth for the version.** `VERSION` comes from
  `[project].version`; a second hard-coded copy is a defect, and the fallbacks
  exist only so an import never raises.
- **The README and `AGENTS.md` are generated.** Edit `automation/readme/README.ejs`
  and the marked sections of `AGENTS.md`, never the rendered files by hand.
- **Repository tooling is Python.** Two npm binaries are pinned in `package.json`
  and driven by Python wrappers: `readme-md-generator` (`automation.readme`) and
  `agents-md` (`automation.agents`).
- **Stable diagnostic codes.** Findings use prefixed codes (`PSF-DOC-###`,
  `PSF-FEAT-###`, `PSF-FORM-###`, `PSF-AGENT-###`) so they can be quoted in
  documentation and tests.
<!-- agents-md:end id=conventions -->

<!-- agents-md:begin id=git -->
## Git & PR workflow

- Conventional Commits, enforced by `convco` in a commit-msg hook and in CI:
  `feat(version)`, `fix(docs)`, `chore(deps)`, `test(readme)`, `docs(development)`.
- One logical change per commit; keep the subject under 72 characters and put the
  reason in the body.
- `CHANGELOG.md` follows Keep a Changelog: add the entry under `Unreleased` in the
  same change, in the section that matches the type of change.
- The pre-commit hook runs lint, format, types, Gherkin, docs, the issue forms,
  README and `AGENTS.md` freshness, alint and actionlint. The pre-push hook runs
  both test suites. Do not bypass a hook to get a commit through.
- A pull request states what changed, why, and which gate proves it.
<!-- agents-md:end id=git -->

<!-- agents-md:begin id=gotchas -->
## Gotchas & hard-won lessons

- **The package is a skeleton.** Reaching for `ShellScript`, a renderer or `psf`
  fails, because they were removed. Add them back through the backlog, with tests
  and docs, rather than from memory.
- **A wheel does not ship `pyproject.toml`.** Reading the version must fall back to
  `importlib.metadata` and then to a constant, or `import pyshellforge` breaks for
  every installed copy. `pyshellforge/tests/unit/test_version.py` pins that order.
- **`pixi run` fails with `Permission denied` when `~/.pixi/bin/pixi` has lost its
  executable bit**, which a restored snapshot does. `python -m automation.restore`
  repairs it; that is what the script is for.
- **The Pixi environment has no pip.** Never add a task that runs
  `python -m pip`; the package comes from `[pypi-dependencies]`, and system
  interpreters may lack the dev extras after a sandbox reset.
- **BDD steps must not assign to module attributes.** An assignment such as
  `generate.install_pixi = ...` persists across tests and fails only in a full-suite
  run. Inject the collaborator instead.
- **A version can be spent once.** PyPI refuses a duplicate, and
  `.github/workflows/release.yml` publishes on a `v*` tag, so
  `pyshellforge/pyproject.toml` must carry the new version before the tag is
  pushed. `python -m automation.release` fails before building when the tag and
  `[project].version` disagree.
- **Doit cannot name a task with a hyphen.** A task's name comes from its
  `task_` function, so every task also sets `basename`; keep that in step with
  the docstring, because `doit list` is the CLI's only documentation.
- **Importing `dodo.py` must stay free of side effects.** doit imports it to
  discover tasks, so a module that does work at import time would run that work
  on every command.
- **`gh form preview` is a manual step.** Without `gh` and `cargo` the forms cannot
  be rendered, so trust `python -m automation.forms` for the schema and say plainly
  that the visual preview did not run.
- **Non-ASCII is unsafe in shell heredocs**; write files through a tool or a Python
  script instead.
<!-- agents-md:end id=gotchas -->

<!-- agents-md:begin id=security -->
## Security & secrets

- Never commit credentials, tokens or private keys. `.github/workflows/` reads
  secrets through `${{ secrets.* }}` only.
- `CHANGELOG.md`, the docs and the tests carry no real hostnames, accounts or keys;
  examples use `example.com` and placeholder paths.
- Reports that could expose untrusted text to a shell are security reports: they go
  to a private advisory, which is what the bug form's checklist says.
- CI runs with `permissions: contents: read` and `persist-credentials: false`.
<!-- agents-md:end id=security -->

<!-- agents-md:begin id=boundaries -->
## Boundaries

- ✅ **Always**: run `pixi run automation check` and `pixi run automation test-all` before reporting a
  change as done; add a scenario and a test with the behaviour; update the canonical
  `docs/` page; regenerate `README.md` and `AGENTS.md` instead of hand-editing
  generated regions; keep `backlog/` status truthful.
- ⚠️ **Ask first**: adding a dependency or a new tool; changing a public API, a
  diagnostic code or the version contract; touching `.github/workflows/`,
  `pixi.toml`, `pyshellforge/tox.ini` or the release configuration; anything that
  pushes, tags
  or publishes. Publishing is trusted publishing (OIDC) from the `pypi`
  environment, so never add an API token.
- 🚫 **Never**: commit secrets or credentials; edit `.tox/`, `.pixi/`,
  `node_modules/`, `dist/` or a generated file by hand; disable a lint rule to
  silence a finding instead of fixing it; describe behaviour that has no code
  behind it.
<!-- agents-md:end id=boundaries -->

## Start each session

Check that Pixi is available, restore it when it is not, then install the hooks:

```sh
command -v pixi || python -m automation.restore
pixi run install-hooks
```

`python -m automation.restore` installs Pixi when it is missing, solves the
environment from `pixi.lock` and installs the Lefthook hooks, so it covers the
second command as well when Pixi was absent. It repairs a `pixi` binary that lost
its executable bit. `python -m automation.restore --check` reports the state and
changes nothing; `--json` prints the same facts as JSON.

Then read, in this order: `backlog/config.yml` and the open tasks (`pixi run
backlog task list --status "To Do" --plain`), `CHANGELOG.md` under `Unreleased`,
`docs/development/testing.md`, and the code you are about to change.

## Issue forms

Bug reports and feature requests use GitHub Issue Forms in
`.github/ISSUE_TEMPLATE/` (`bug_report.yml`, `feature_request.yml`), with
`config.yml` adding the contact links and disabling blank issues. The forms ask
for the version, the interpreter, the area and a minimal reproduction, because a
report without them cannot be reproduced.

```sh
pixi run automation check-forms    # python -m automation.forms; also part of `pixi run automation check`
gh form preview         # render the form locally; needs gh, never run in CI
```

`python -m automation.forms` implements GitHub's schema offline and reports
`PSF-FORM-###` codes. Keep YAML Issue Forms only: Markdown issue templates and
pull request templates are out of scope, and `gh form preview` covers neither.

## Documentation quality

`docs/` is maintained, not an afterthought. Every change that touches behaviour,
configuration or a workflow includes a documentation impact assessment, and the
canonical page is updated rather than duplicated.

```sh
pixi run automation check-docs       # structure, navigation, links, anchors (Python)
pixi run automation lint-markdown    # markdownlint-cli2
pixi run automation lint-prose       # Vale + Microsoft style
pixi run automation lint-links       # lychee: external links and fragments
pixi run automation alint            # repository conventions
```

The tree is small on purpose: `docs/README.md` indexes `docs/development/`, and the
user-facing sections come back with the code they document. Add legitimate project
terms to `.vale/styles/config/vocabularies/Project/accept.txt`; never disable a
rule to silence a finding. The policy is in
[`docs/development/documentation.md`](docs/development/documentation.md).

## Notes

<!-- Human-owned. Anything here is never touched by re-runs of agents-md. -->

- The marked sections above are the `agents-md` contract: the CLI rewrites them,
  everything outside them is hand-owned and preserved. `pixi run automation agents` runs the
  CLI, `pixi run automation agents-check` validates the result offline in CI.
- This file is curated inside the markers rather than left as a raw scan. The scanner reads npm and Python manifests; this repository's truth lives
  in `pixi.toml`, `pyshellforge/tox.ini` and `automation/`, so an unedited scan would
  replace
  working guidance with placeholder text. `automation.agents` fails the build if
  a stub, a missing marker or a stale `AGENTS.generated.md` sidecar reappears.
- `AGENTS.md` is the single source. No `CLAUDE.md` symlink is created: symlinks in
  a Git checkout need platform-specific setup, and every agent that matters reads
  `AGENTS.md` directly.
- `main` takes pull requests by rebase: `gh pr merge --rebase <number>`. Never
  create a merge commit — GitHub's `Merge pull request #N from ...` subject is not
  a Conventional Commit, and the `Reject merge commits on main` step in
  `ci.yml` fails the push that adds one. Details in
  [`docs/development/contributing.md`](docs/development/contributing.md#merging).
- `gh form preview` is a manual step. In a sandbox without `gh` and `cargo` the
  forms cannot be rendered, so trust `python -m automation.forms` for the schema and
  say plainly that the visual preview did not run.

---

<!-- Maintained with agents-md (https://github.com/eugeniughelbur/agents-md).
     Content inside agents-md:begin/end markers is regenerated by the CLI.
     Everything outside the markers, including these Notes, is human-owned. -->
