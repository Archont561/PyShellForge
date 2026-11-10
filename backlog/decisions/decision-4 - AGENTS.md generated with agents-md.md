---
id: decision-4
title: AGENTS.md is generated with agents-md and validated by a Python wrapper
date: 2026-11-09
status: Accepted
references: [AGENTS.md, automation/agents/generate.py, automation/features/agents_file.feature, docs/development/documentation.md]
---

## Context

`AGENTS.md` had grown into a hand-written document with the session ritual, the
backlog workflow, the engineering rules and the command table. A hand-written
file drifts: a renamed task, a new gate or a changed command stays wrong until
somebody notices. The `agents-md` CLI exists for exactly this, and its marker
contract (`<!-- agents-md:begin id=... -->`) lets a re-run refresh the sections it
produced while leaving hand-written text alone.

Three facts about the CLI shaped the integration:

1. It reads `package.json`, `pyproject.toml` and the directory tree.
2. It marks anything it cannot detect as `_TBD:` and rewrites the whole marked
   region on every run.
3. Given an `AGENTS.md` without markers it writes `AGENTS.generated.md` instead
   of touching the file.

## Decision

Adopt the marker contract, curate the marked sections, and validate the result
with our own Python wrapper.

- `AGENTS.md` carries all nine sections the CLI knows (`overview`, `commands`,
  `testing`, `structure`, `conventions`, `git`, `gotchas`, `security`,
  `boundaries`), each inside its markers, with real content instead of the
  scanner's placeholders. Human-owned material (the session ritual, the backlog
  survey, the documentation policy, `## Notes`) sits outside the markers.
- `automation.agents --bootstrap` (`pixi run automation agents`) runs the pinned CLI to create
  the skeleton and refuses to overwrite a file that already has markers unless
  `--force` is passed, because a re-run replaces curated text with scan output.
- `automation.agents --check` (`pixi run automation agents-check`) enforces the contract
  offline: every section present and in the CLI's order, headed as the CLI
  expects, non-empty, free of `_TBD:` stubs, and no stale sidecar. It runs in the
  pre-commit hook, in the CI docs job and in `pixi run automation check`.
- Diagnostics are stable codes `PSF-AGENT-001` to `PSF-AGENT-007`, in the same
  style as `PSF-DOC-###` and `PSF-FEAT-###`.
- No `CLAUDE.md` symlink: the CLI creates one, but symlinks in a Git checkout need
  platform setup and every relevant agent reads `AGENTS.md` directly, so the
  wrapper passes `--no-symlink`.

## Consequences

- `AGENTS.md` keeps the CLI's structure, so a future re-run, upgrade or
  hand-off lands in a shape the tool understands.
- The wrappers stay Python, tested in `automation/tests/test_agents.py` and
  described in `automation/features/agents_file.feature`, which honours the
  Python-only tooling rule.
- Curated text inside the markers is destroyed by `--force`; that is documented
  in the file itself and in the contributing guide, and the check makes the damage
  visible instead of silent.
- The file cannot silently lose a section, gain a placeholder or start shadowing
  a generated sidecar.

## Alternatives considered

- **Let the CLI own the file and accept its output.** Rejected: for this
  repository it emits `_TBD:` placeholders in seven of nine sections and reports
  the stack as Node, because the commands live in `pixi.toml` and `pyshellforge/tox.ini`. The
  file would lose the guidance it exists for.
- **Keep the file fully hand-written and ignore the tool.** Rejected: the user
  asked for generation and maintenance, and the marker contract is a good idea
  whether or not the scanner can see Pixi.
- **Run the LLM-powered skill mode in CI.** Rejected: CI needs a deterministic,
  offline check, not a model call.
