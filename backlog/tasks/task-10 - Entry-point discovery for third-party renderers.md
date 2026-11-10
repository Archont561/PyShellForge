---
id: task-10
title: Entry-point discovery for third-party renderers
status: To Do
labels: [plugins, api]
created_date: 2026-11-09
dependencies: [task-8, task-9]
references: [src/pyshellforge/backends/__init__.py, docs/architecture/multi-shell.md]
---

## Description

The registry is the seam for plugins, and it is still filled by hard-coded imports
in `backends/__init__.py::_BACKENDS`. Once a second non-Bash renderer exists, the
contract stops being a guess and can be published as entry points.

## Acceptance criteria

- [ ] `pyshellforge.backends` entry point group: a distribution registers a
      `ShellBackend` subclass, discovered with `importlib.metadata`.
- [ ] `available_backends()` reports built-in and installed targets separately, and
      `psf render --shell unknown` lists both.
- [ ] A test distribution under `tests/data/plugin_package/` proves discovery,
      version mismatch, and a failing import that is reported rather than raised
      during rendering.
- [ ] `docs/architecture/multi-shell.md` and `CONTRIBUTING.md` describe writing a
      plugin distribution.

## Definition of done

- [ ] Docs, tests, `CHANGELOG.md`, and the plugin page in `docs/reference/`.
