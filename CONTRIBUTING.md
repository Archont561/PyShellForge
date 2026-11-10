# Contributing

Thanks for helping! The full guide lives in [`docs/contributing.md`](docs/development/contributing.md);
this page is the short version.

## Quick start

```bash
git clone https://github.com/Archont561/PyShellForge
cd PyShellForge
pixi install --locked
pixi run install-hooks
pixi run automation test-all       # both suites
pixi run automation check          # every check, as one task graph
```

Plain pip works too: `python -m venv .venv && . .venv/bin/activate`,
`pip install -e "pyshellforge[dev]"`, then
`python -m pytest -c pyshellforge/pyproject.toml pyshellforge/tests automation/tests`.

## What we care about

* **Deterministic, readable output.** A rendering change must keep
  the integration test suite green and the Bash block in the README in step
  with the Python block above it.
* **Quoting safety.** Untrusted text must never become shell syntax; `RawShell`
  is the only escape hatch and it is explicit.
* **No execution at render time.** The renderer is a pure function of the tree.
* **Tests for every node**—rendering, quoting, validation, and where sensible
  an integration test that runs the generated script.

## Merging

Pull requests are merged with rebase (`gh pr merge --rebase <number>`), so `main`
stays linear and every commit on it is one the review saw. A merge commit is
rejected by CI, and a squash merge would collapse a reviewed series into one
commit. Details in
[`docs/contributing.md`](docs/development/contributing.md#merging).

## The README is generated

`README.md` and `pyshellforge/README.md` come from
[`automation/readme/README.ejs`](automation/readme/README.ejs) via
readme-md-generator, driven by the Python module `python -m automation.readme` with
metadata from `package.json`:

```bash
pixi run automation readme          # rewrite README.md
pixi run automation readme-check    # fail if it is stale (CI does this)
```

Edit the template or `package.json`, never `README.md` directly. Details in
[`docs/contributing.md`](docs/development/contributing.md#regenerating-the-readme).

## Adding behaviour

The package is a skeleton: `pyshellforge/src/pyshellforge/__init__.py` exposes `VERSION` and nothing
else. Behaviour comes back through `backlog/`, and a change is complete only when
all of these are true:

1. The code exists, typed, with a docstring that explains why it is there.
2. A test proves it: a unit test for the logic, an execution test when only a real
   process can prove the behaviour.
3. The canonical `docs/` page describes it, and `docs/README.md` links to that page.
4. A Gherkin scenario in `automation/features/` covers the user-visible part,
   with its step definition in `automation/tests/bdd/` and that module added to the
   list `automation/tests/bdd/conftest.py` imports.
5. `CHANGELOG.md` records it under `Unreleased`.

## Reporting bugs

Include the version from
`python -c "import pyshellforge; print(pyshellforge.VERSION)"`, `python -V`, your
operating system, and what you ran, expected and got.

## Security

A `Literal` that renders as shell syntax is a security bug—please use a private
security advisory instead of a public issue.

## Style

Python 3.11+, type annotations everywhere (mypy strict), ruff for lint and
format, line length 100, imperative commit messages such as
`fix(renderer): never indent a here-doc delimiter`.
