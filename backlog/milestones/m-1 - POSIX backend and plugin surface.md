---
id: m-1
title: POSIX backend and plugin surface
status: In Progress
---

## Goal

Make the POSIX backend a first-class target and finish the documented plugin
surface, so PyShellForge can render `/bin/sh` scripts without silently emitting
Bash-only syntax and third parties can add nodes without forking the renderer.

## Outcome

A user can render with `--shell posix`, get either portable output or a clear
`UnsupportedNodeError`, and follow one canonical guide for adding a node.

## Tasks

- `task-1`—POSIX backend hardening
- `task-2`—Plugin API documentation
