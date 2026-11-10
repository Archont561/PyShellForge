# Linting

A definition is Python, so the conventions that keep the generated script
readable can be checked while it is still Python: in an editor, in a pre-commit
hook and in CI, without importing the package or rendering anything.

The repository separates three layers, and each one answers a question the others
cannot.

| Layer | Answers | Lives in | State |
| --- | --- | --- | --- |
| Scope casing | Does the case of a name match the scope it renders as? | [`pyshellforge-rude/`](../../pyshellforge-rude/), a Rude plugin | shipped |
| Repository checks | Formatting, types, prose, links, documentation structure | `automation/`, ruff, mypy, markdownlint, Vale | shipped |
| Semantic validation | Unused names, constructs the target cannot express, unsafe expansions | `psf validate` | not implemented, see [`backlog/`](../../backlog/) |

## The Rude plugin

[Rude](https://docs.rude.dev) is a Python linter that runs custom rules in Python
against a semantic model of the file. `pyshellforge-rude` registers two rules
through Rude's `rude.plugins` entry point, so installing the distribution is the
whole setup:

```console
pip install pyshellforge-rude
rude check src/
```

Rude discovers installed plugins by itself. To run only these rules:

```console
rude check --select PSF src/
```

Or select them from `pyproject.toml`:

```toml
[tool.rude]
select = ["PSF"]
```

| Code | Rule | Why it exists |
| --- | --- | --- |
| `PSF201` | A module-level binding is `UPPER_CASE` | Module scope becomes the global scope of the script |
| `PSF202` | A function-scoped binding is `lower_case` | Function scope becomes a `local` |

The two rules are a pair. On its own, either one is a style preference; read
together they say that a name's case is how a reader sees its scope, which is a
fact the generated script cannot carry in the name. Shell users already read case
that way: `PATH` and `HOME` are globals, loop counters are locals.

Both rules report at warning severity, so they inform a build without breaking
it, and both run only in files that mention `pyshellforge` or `@sh`. Installing
the plugin therefore does not re-case the other Python files in a repository.

```python
from pyshellforge import Int, Path, Str, sh

NAME: Str = "release"          # accepted: becomes a global
target_dir: Path = "/srv/app"  # PSF201: name it TARGET_DIR


@sh
def build(jobs: Int = 4) -> None:
    TMP = 1                    # PSF202: name it tmp
```

### What the rules leave alone

- Imports and type aliases, because they do not become shell variables.
- Class attributes, because a class is not a script scope.
- Module-level `for` and `with` targets, which the compiler decides on.
- Tuple, attribute and subscript targets, whose render is the compiler's business.
- Names declared `global` or `nonlocal`, because the declaring scope decides the case.
- `self`, `cls` and `_`.

## What the plugin cannot see

The plugin reads Python syntax and scope, and nothing else. It does not know the
target shell, the declared type of a binding, whether a name is ever used, or what
the rendered script looks like. Rules that need any of those belong to
`psf validate`, which reads the definition with the compiler's own type and
capability tables; adding one here would duplicate that knowledge in a second
engine and drift from it.

The reverse direction matters too. Anything the renderer already guarantees — a
quoted expansion, `set -euo pipefail` in the preamble — is a test over the
renderer, not a lint rule about a definition.

## Working on the plugin

```console
pip install -e "pyshellforge-rude[dev]"
python -m pytest -c pyshellforge/pyproject.toml pyshellforge-rude/tests
```

The rules are tested through Rude's public `Linter` API, so a test feeds a
definition fragment to `check_source` and asserts on codes and lines. `.coveragerc`
measures `pyshellforge_rude` in the same run as the rest of the repository, and
`mypy` and ruff cover `pyshellforge-rude/src` from the repository root.

Back to the [documentation index](../README.md).
