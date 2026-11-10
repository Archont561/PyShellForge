---
id: task-14
title: Command line interface
status: To Do
labels: [cli, dx]
created_date: 2026-11-10
dependencies: [task-11, task-13]
references: [pyshellforge/pyproject.toml, docs/reference/linting.md, automation/detect_changes.py]
---

## Description

The `psf` entry point: render a definition, validate it, inspect its tree, and
list the backends it can render to. The surface is the one the project listed
before the reduction to a skeleton (`render`, `validate`, `inspect`, `version`),
plus `backends`, which turns "does this target exist" into a question the CLI
answers instead of a traceback.

The framework is `argparse` from the standard library. The package declares
`dependencies = []`, every module under `automation/` is already argparse with an
injectable `main(argv)`, and `psf validate` will run in pre-commit where import
cost matters. Rich output is worth having, so color and tables arrive through an
optional `pretty` extra that is imported only when writing to a terminal; without
it the output is plain text.

The contract matters more than the commands: the artifact goes to stdout, the
diagnostics go to stderr, so `psf render app.py > app.sh` works, and the exit
codes are stable enough to script against.

## Files

- `pyshellforge/src/pyshellforge/cli/` for the parser, one module per command and
  the output formatting
- `pyshellforge/src/pyshellforge/__main__.py` for `python -m pyshellforge`
- `docs/reference/cli.md` for the commands, the flags and the exit codes
- `pyshellforge/tests/integration/test_cli.py` for the end-to-end runs

## Acceptance criteria

- [ ] `psf render FILE|-` writes the script to stdout and takes `--shell`, `-o`,
      `--indent`, `--shebang/--no-shebang`, `--source-comments` and `--check`.
- [ ] `--check` exits non-zero when the file on disk differs from what would be
      rendered, without writing anything.
- [ ] `psf validate` prints diagnostics to stderr and takes `--json`, `--strict`,
      `--shell` and `--color always|auto|never`, honoring `NO_COLOR`.
- [ ] `psf inspect` dumps the node tree, with `--json` for tooling.
- [ ] `psf backends` lists the available targets and their capability gaps.
- [ ] `-` reads a definition from stdin, and `--stdin-filename` keeps diagnostic
      paths useful for an editor.
- [ ] Exit codes: `0` success, `1` findings or a stale render, `2` usage error.
- [ ] `--json` never imports the `pretty` extra and never emits color.
- [ ] `[project.scripts]` declares `psf` and `psf --version` reports `VERSION`.

## Definition of done

- [ ] One test per command, including the stdout/stderr split and the exit codes.
- [ ] `docs/reference/cli.md` is linked from the index.
- [ ] `CHANGELOG.md` records the CLI under `Unreleased`.
