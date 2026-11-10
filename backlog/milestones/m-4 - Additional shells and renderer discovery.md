---
id: m-4
title: Additional shells and renderer discovery
status: To Do
---

## Goal

Extend the backend contract beyond Bash and POSIX, and demonstrate how a
third-party renderer can be discovered.

## Outcome

Zsh and fish have tested renderers and documented capability gaps. Backend
capabilities and artifact policies are explicit, third-party renderer discovery
is available, and an external PowerShell proof demonstrates the extension path
without claiming full shell parity.

## Dependencies

The work builds on `task-11` in `m-2` and on the POSIX and plugin work in `m-1`.
The discovery task follows the Zsh and fish renderers. The PowerShell proof also
needs the discovery path and the constructs described in `task-17`.

## Tasks

- `task-8`: Zsh renderer
- `task-9`: fish renderer
- `task-10`: Entry-point discovery for third-party renderers
- `task-17`: Backend capability matrix and the PowerShell proof
