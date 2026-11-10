---
id: task-10
title: Entry-point discovery for third-party renderers
status: To Do
labels: [plugins, api]
created_date: 2026-11-09
dependencies: [task-8, task-9]
milestone: m-4
references: [packages/pyshellforge/pyproject.toml, CONTRIBUTING.md]
---

## Description

Entry points are the public form of the registry seam. A second non-Bash renderer
is what turns the backend contract from a guess into a fact, so this task waits on
`task-8` and `task-9` before it publishes the `pyshellforge.backends` group.

## Acceptance criteria

- [ ] `pyshellforge.backends` entry point group: a distribution registers a
      `ShellBackend` subclass, discovered with `importlib.metadata`.
- [ ] `available_backends()` reports built-in and installed targets separately, and
      `psf render --shell unknown` lists both.
- [ ] A test distribution under `packages/pyshellforge/tests/data/plugin_package/` proves discovery,
      version mismatch, and a failing import that is reported rather than raised
      during rendering.
- [ ] `docs/reference/backends.md` and `CONTRIBUTING.md` describe writing a plugin
      distribution.

## Files

- `packages/pyshellforge/src/pyshellforge/backends/__init__.py`
- `packages/pyshellforge/tests/data/plugin_package/`

## Definition of done

- [ ] Docs, tests, `CHANGELOG.md`, and the plugin page in `docs/reference/`.
