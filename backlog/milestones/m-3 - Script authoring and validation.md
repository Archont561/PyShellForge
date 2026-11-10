---
id: m-3
title: Script authoring and validation
status: To Do
---

## Goal

Extend the Bash foundation with useful script constructs, diagnostics, a command
line interface and helpers for testing definitions.

## Outcome

A user can express the constructs covered by the assigned tasks, validate a
definition, render it from the command line and test its output. Individual tasks
still define the supported constructs and their acceptance criteria; this
milestone does not promise the complete DSL.

## Dependencies

The tasks follow `task-11` in `m-2`. The command line interface also waits for the
validation engine (`task-13`). Additional construct-specific prerequisites remain
in their task descriptions.

## Tasks

- `task-4`: Add Select and ForC loop nodes
- `task-13`: Validation engine and rule families
- `task-14`: Command line interface
- `task-15`: Testing helpers for definitions
- `task-16`: DSL surface, the first wave
