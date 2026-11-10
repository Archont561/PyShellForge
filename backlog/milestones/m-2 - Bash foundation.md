---
id: m-2
title: Bash foundation
status: In Progress
---

## Goal

Establish the core engine and a Bash renderer that can produce a small script
from structured nodes, with repeatable checks on the generated output.

## Outcome

A user can build and render comments, variable assignments, commands and `Echo`
as Bash. The renderer's output is tested for syntax and canonical formatting, and
the core API is documented. This is the foundation for the other product
milestones, not a claim that the full DSL is complete.

## Tasks

- `task-11`: Core engine, AST base and Bash renderer
- `task-3`: Verify rendered output with shfmt in CI (after `task-11`)
