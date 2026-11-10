# Project status

**What exists today is the skeleton.** The package ships one module,
`pyshellforge/src/pyshellforge/__init__.py`, and it exposes one attribute:

```python
>>> import pyshellforge
>>> pyshellforge.VERSION
'0.1.0'
```

`VERSION` is read from `[project].version` in `pyproject.toml` when the package
runs from a source checkout, falls back to installed distribution metadata, and
last to a constant, so an import never fails.

The one thing beyond the skeleton is a second distribution, `pyshellforge-rude/`:
a Rude plugin that checks the two casing conventions a definition has to keep, so
a module-level binding is `UPPER_CASE` and a function-scoped one is `lower_case`.
It needs no renderer, which is why it could ship first; see
[Linting](../reference/linting.md).

There is no renderer, no AST and no CLI yet, and nothing in the documentation
describes one. The work that would
change that is tracked in [`backlog/`](../../backlog/) and
[`CHANGELOG.md`](../../CHANGELOG.md), and the target is a Python-native DSL that
builds structured Bash: you describe the script as objects and the library
renders shell text you can review.

## Roadmap

| Phase | Scope | State |
| --- | --- | --- |
| 0 | Skeleton: one module, `VERSION` read from `pyshellforge/pyproject.toml` | done |
| 1 | Core engine: AST base, `ShellScript`, Bash renderer, comments, variables, commands | planned |
| 2 | Functions, expressions, conditions, loops, arrays | planned |
| 3 | Pipes, redirects, heredocs, subshells, command substitution | planned |
| 4 | Validation, diagnostics, CLI, `bash -n` in CI | planned |
| 5 | Documentation, packaging, custom renderers | planned |

Phase 1 is `task-11` in [`backlog/tasks/`](../../backlog/tasks/): the AST base,
`ShellScript` and the Bash renderer for comments, variables and commands. The
POSIX backend, the shell renderers and the plugin surface all wait on it, which
is why the roadmap has nothing to report beyond phase 0.

Back to the [documentation index](../README.md).
