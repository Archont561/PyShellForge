---
id: task-15
title: Testing helpers for definitions
status: To Do
labels: [testing, api]
created_date: 2026-11-10
dependencies: [task-11]
milestone: m-3
references: [packages/pyshellforge/pyproject.toml, docs/development/testing.md]
---

## Description

A user who builds a script with this library needs to test it, and the assertions
are always the same four: this script renders to that text, this definition is
valid, this construct is refused, and running the script produces this output.

`pyshellforge.testing` is the public home for those four, shipped inside the
existing wheel and importing only the standard library. The repository's own
fixtures stay in `packages/pyshellforge/tests/conftest.py`: same word, different audience.

The helper that matters is the last one. Rendering and comparing text proves the
renderer and the test agree; running the result through a real shell proves the
script is a script.

## Files

- `packages/pyshellforge/src/pyshellforge/testing/__init__.py` for the helpers
- `packages/pyshellforge/src/pyshellforge/testing/pytest_plugin.py` for the fixtures
- `docs/reference/testing.md` for the public API, separate from
  `docs/development/testing.md`, which describes this repository's suite
- `packages/pyshellforge/tests/integration/test_testing.py` for the helpers tested against
  themselves

## Acceptance criteria

- [ ] `render(script, shell=...)` returns the text, and `assert_renders` compares
      it with a diff that shows the first differing line and makes trailing
      whitespace visible.
- [ ] `bash_syntax` runs `bash -n` (or `dash -n`) and skips, rather than fails,
      when the shell is absent.
- [ ] `run_script` writes a temporary file, runs it with the default environment
      copied and `LC_ALL=C`, and returns the completed process.
- [ ] `assert_runs` checks stdout, the exit status and the files a script leaves
      behind.
- [ ] `assert_matches_golden` writes on `PSF_UPDATE_GOLDENS=1` and the golden path
      carries the dialect, so a golden cannot be compared to the wrong backend.
- [ ] Every helper raises `AssertionError` explicitly, never with a bare `assert`,
      because `python -O` strips assertions.
- [ ] A `pytest11` entry point provides `psf_bash` and `psf_render`, registers its
      markers, and imports pytest only inside the plugin module.

## Definition of done

- [ ] The helpers are used by the repository's own integration suite.
- [ ] `docs/reference/testing.md` is linked from the index.
- [ ] `CHANGELOG.md` records the module under `Unreleased`.
