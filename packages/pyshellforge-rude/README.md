# pyshellforge-rude

PyShellForge conventions as rules for the [Rude](https://docs.rude.dev) Python
linter, so a definition is checked in an editor and in CI without running the
compiler.

```console
pip install pyshellforge-rude
rude check src/
```

Rude discovers the plugin through its `rude.plugins` entry point, so there is no
configuration step. To run only these rules:

```console
rude check --select PSF src/
```

## Rules

| Code | Rule | Why |
| --- | --- | --- |
| `PSF201` | Module-level bindings are `UPPER_CASE` | A module-level binding becomes a global shell variable |
| `PSF202` | Function-scoped bindings are `lower_case` | A binding inside a function becomes a `local` |

The two rules are a pair. Together they say that a name's case tells a reader its
scope in the generated script, which is a fact the script itself cannot carry.
Both run only in files that mention `pyshellforge` or `@sh`, so installing the
plugin does not re-case every Python file in a repository. Both report at warning
severity, so they inform a build without breaking it.

```python
from pyshellforge import Int, Path, Str, sh

NAME: Str = "release"          # PSF201 accepts: becomes a global
target_dir: Path = "/srv/app"  # PSF201: name it TARGET_DIR


@sh
def build(jobs: Int = 4) -> None:
    TMP = 1                    # PSF202: name it tmp
```

## Scope

These rules check Python syntax and scope only. Everything that depends on
PyShellForge semantics, such as a name declared but never used, a construct the
target shell cannot express, or an unset value reaching `rm`, belongs to `psf validate`,
which the compiler owns. See the
[linting reference](https://github.com/Archont561/PyShellForge/blob/main/docs/reference/linting.md).

## Development

```console
pip install -e ".[dev]"
python -m pytest tests -q
```

The package is versioned and released from the
[PyShellForge repository](https://github.com/Archont561/PyShellForge); Rude is
pinned below `0.2` because a plugin is the first thing a pre-1.0 rule API
breaks.
