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

## Reading order

[`docs/concepts/version-only-scaffold.md`](../docs/concepts/version-only-scaffold.md)
says what exists and what each roadmap phase adds. This directory says what the
next change is.
