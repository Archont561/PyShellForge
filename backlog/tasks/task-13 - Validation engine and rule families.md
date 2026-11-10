---
id: task-13
title: Validation engine and rule families
status: To Do
labels: [validation, diagnostics, core]
created_date: 2026-11-10
dependencies: [task-11]
references: [pyshellforge/src/pyshellforge/__init__.py, docs/reference/linting.md, backlog/decisions/decision-6 - Lint rules ship as a Rude plugin.md]
---

## Description

The engine that answers the questions a linter reading Python syntax cannot: is
this name used, does this construct exist in the target shell, and can this value
reach that command.

It needs the symbol table and the capability table, so it follows `task-11`. It
also fixes the code families that decision-6 and the plugin already assume:
`PSF1xx` structure, `PSF2xx` names, `PSF3xx` context and portability, `PSF4xx`
safety. `PSF201` and `PSF202` exist in `pyshellforge-rude`; the validator must
implement the same codes with the same meaning, not new ones.

The safety family is the reason the validator is worth building. A shell linter
sees the rendered `"$TARGET"` and calls it correctly quoted; the compiler knows
`TARGET` came from an option, may be empty, and is about to reach `rm -rf`.

## Files

- `pyshellforge/src/pyshellforge/validation/` for `Diagnostic`, `DiagnosticBag`,
  `Severity`, the rule decorator and the context tracker
- `pyshellforge/src/pyshellforge/validation/rules/` for one module per family
- `docs/reference/diagnostics.md` for the code table and the severity meanings
- `pyshellforge/tests/unit/validation/` for one test module per rule

## Acceptance criteria

- [ ] A diagnostic carries a stable code, a severity, a message and a location
      that resolves to a node path (`script[3].body[0]`), not only a line.
- [ ] Rules register by decorator and can inspect the enclosing context:
      function, loop, case and duplicate function names.
- [ ] `PSF201` and `PSF202` reproduce the plugin's results, so the same definition
      gets the same finding from either engine.
- [ ] `PSF3xx` reads a capability table per backend: arrays and `=~` are refused
      on POSIX, process substitution on POSIX, and a refusal names the construct
      and the target.
- [ ] `PSF4xx` flags an empty or unset expansion reaching a destructive command,
      `eval`, and a pipeline into a shell.
- [ ] Severity is a property of the rule, and `--strict` promotes warnings.

## Definition of done

- [ ] One test per code, plus a test that a clean script produces no diagnostics.
- [ ] `docs/reference/diagnostics.md` lists every code and is linked from the index.
- [ ] `CHANGELOG.md` records the engine under `Unreleased`.
