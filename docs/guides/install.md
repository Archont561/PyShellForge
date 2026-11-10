# Install

## Prerequisites

- python: `>=3.11`, from `requires-python` in
  [`pyshellforge/pyproject.toml`](../../pyshellforge/pyproject.toml).

No shell is a prerequisite yet, because nothing renders shell: the package
exposes `VERSION` and nothing else. [Project status](../concepts/version-only-scaffold.md)
says what exists today and what the roadmap adds.

## Install the package

```sh
pip install pyshellforge
```

## Use it

```sh
python -c "import pyshellforge; print(pyshellforge.VERSION)"
```

## Work on the repository

The locked environment is what the hooks and CI use, so prefer it when you
change the repository:

```sh
command -v pixi || python -m automation.restore   # installs Pixi, solves the env
pixi run install-hooks                           # Lefthook git hooks
```

`pip install -e "pyshellforge[dev]"` works too when you do not want Pixi. The
task catalogue is [Tooling](../development/tooling.md), and the checks a change
has to pass are [Contributing](../development/contributing.md).

Back to the [documentation index](../README.md).
