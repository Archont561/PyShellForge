# Install

## Prerequisites

- python: `>=3.11`, from `requires-python` in
  [`packages/pyshellforge/pyproject.toml`](../../packages/pyshellforge/pyproject.toml).

The renderer produces Bash scripts; running those scripts requires Bash. Importing
and rendering with the package does not require a shell. [Project status](../concepts/version-only-scaffold.md)
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

`pip install -e "packages/pyshellforge[dev]"` works too when you do not want Pixi. The
task catalogue is [Tooling](../development/tooling.md), and the checks a change
has to pass are [Contributing](../development/contributing.md).

Back to the [documentation index](../README.md).
