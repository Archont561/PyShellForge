---
id: decision-1
title: One package with a renderer and backend per shell
date: 2026-11-09
status: Accepted
references: [packages/pyshellforge/pyproject.toml, packages/pyshellforge/src/pyshellforge/__init__.py]
---

## Context

PyShellForge renders a shell-neutral AST. Bash is the reference target, POSIX
`sh` is experimental, and Zsh, fish and PowerShell are planned. That raised a
packaging question: does each shell ship as its own distribution
(`pyshellforge-bash`, `pyshellforge-fish`, ...), or does one package carry a
renderer per target?

## Decision

One package. `pyshellforge` declares a `ShellBackend` per target in
`backends/__init__.py::_BACKENDS`, and each backend names the renderer class it
instantiates. Nodes do not change per target: a renderer either emits the
construct or raises `UnsupportedNodeError` naming the node, the target and the
portable alternative.

Third-party nodes and renderers plug in through public seams (`register_renderer`,
`register_node_type`, `ShellScript(renderer=...)`), so a later move to
`importlib.metadata` entry-point discovery is additive.

## Consequences

- A node is not "done" until Bash renders it; other targets may reject it with a
  documented `UnsupportedNodeError`, listed in the capability matrix.
- A target counts as supported only when CI runs its generated scripts through
  the real interpreter.
- One installer, one version, one dependency to audit. Install size stays a few
  hundred kilobytes.
- Adding a shell is one renderer module, one backend record and one test module,
  not a repository, a release train and a second lock file.

## Alternatives considered

- **One distribution per shell.** Rejected: every user pays in version skew and
  N installs, while the shared AST still forces a pin on the core package. The
  freedom it buys is theoretical because the node set is shared anyway.
- **Core plus entry-point plugins immediately.** Deferred, not rejected: freezing
  a plugin contract before a second non-Bash renderer exists would freeze a guess.
  The registry is the seam, and `task-10` schedules the move.

The long form of this decision lived on a page of its own. That page went with the
implementation when the package was reduced to its skeleton; the capability matrix comes
back as `docs/reference/backends.md` with the second renderer (`task-8`).
