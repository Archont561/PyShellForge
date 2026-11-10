# Backlog

Planned work for the library, kept as Markdown with YAML front matter so a task
can be reviewed in a pull request like any other file. The
[Backlog.md](https://github.com/MrLesk/Backlog.md) CLI reads the format
(`pixi run backlog task list --plain`), and `config.yml` holds its settings.

## What is here

| Path | Holds |
| --- | --- |
| `tasks/` | One file per task, named `task-<id> - <title>.md` |
| `milestones/` | A goal and its outcome, plus the tasks that deliver it |
| `decisions/` | Context, decision, consequences and alternatives, dated |
| `config.yml` | Statuses, date format and the project name |

## Statuses

`config.yml` defines three: `To Do`, `In Progress` and `Done`. A task is `In
Progress` only while somebody is working on it, and `Done` only when its
definition of done holds, which includes tests, documentation and a changelog
entry. Nothing here may describe behaviour the tree does not have, so a task that
waits on unimplemented code stays `To Do` however detailed its criteria are.

## Conventions

- `references` lists repository paths that exist today, so every link in the
  backlog opens. Files a task will create belong in a `## Files` section of its
  body.
- `dependencies` lists task ids that must be `Done` first. `task-11`, the core
  engine, is the root of most of the graph.
- `milestone` names the milestone a task delivers, where one applies.
- Prose goes through the same linters as the rest of the repository. `backlog/` counts as
  documentation scope in `automation/detect_changes.py`, so a change limited to
  this directory never triggers the interpreter matrix.

## Milestones

A milestone groups tasks around an outcome; it is not a release date or a change
in task status. A milestone is complete when its assigned tasks meet their own
definitions of done. Dependencies remain on the tasks, including dependencies
between milestones. The order below is a suggested sequence, not a schedule:

| Milestone | Outcome | Tasks |
| --- | --- | --- |
| [m-2: Bash foundation](<milestones/m-2 - Bash foundation.md>) | A small script renders as tested, formatted Bash | 11, 3 |
| [m-1: POSIX backend and plugin surface](<milestones/m-1 - POSIX backend and plugin surface.md>) | Portable output, a documented plugin surface and the Rude plugin | 1, 2, 12 |
| [m-3: Script authoring and validation](<milestones/m-3 - Script authoring and validation.md>) | More constructs, diagnostics, CLI and testing helpers | 4, 13–16 |
| [m-4: Additional shells and renderer discovery](<milestones/m-4 - Additional shells and renderer discovery.md>) | Zsh, fish and a third-party renderer proof | 8–10, 17 |
| [m-5: CI security and coverage](<milestones/m-5 - CI security and coverage.md>) | Pinned actions and combined matrix coverage | 6, 7 |

The foundation precedes the POSIX and script-authoring work. The shell and
renderer-discovery work builds on the foundation and POSIX/plugin work. CI
security and coverage can proceed independently. `task-12` is already in progress
and can also proceed independently of the foundation.

## Reading order

[`docs/concepts/version-only-scaffold.md`](../docs/concepts/version-only-scaffold.md)
says what exists and what each roadmap phase adds. This directory says what the
next change is.
