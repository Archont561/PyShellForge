# Project status

PyShellForge has a small Bash foundation: `ShellScript` collects structured
comments, assignments, commands and `Echo` templates, and `BashRenderer` renders
them as a script. The [API reference](../reference/api-reference.md) describes
the supported subset and its limits. There is no CLI or other shell renderer yet.

`VERSION` comes from `[project].version` when the package runs from a source
checkout, falls back to installed distribution metadata, and last to a constant.
The separate `pyshellforge-rude` distribution provides two casing rules; see
[Linting](../reference/linting.md).

## Roadmap

| Phase | Scope | State |
| --- | --- | --- |
| 0 | Skeleton and version resolution | done |
| 1 | Core engine, AST base, Bash renderer and initial nodes | implemented |
| 2 | Functions, expressions, conditions, loops, arrays | planned |
| 3 | Pipes, redirects, heredocs, subshells, command substitution | planned |
| 4 | Validation, diagnostics and CLI | planned |
| 5 | Additional backends and custom renderers | planned |

The Bash foundation and its remaining checks are tracked in `m-2` in
[`backlog/`](../../backlog/). Further work stays in the backlog; the current
renderer does not imply that later roadmap phases are complete.

Back to the [documentation index](../README.md).
