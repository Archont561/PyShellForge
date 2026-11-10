---
id: task-2
title: Plugin API documentation
status: To Do
milestone: m-1
labels: [docs, plugins]
created_date: 2026-11-09
dependencies: [task-1]
references: [docs/README.md, CONTRIBUTING.md, docs/concepts/version-only-scaffold.md]
---

## Description

The plugin contract is the promise that a third party adds a node without
forking the renderer: a dataclass node, a `render_<snake_case>` method or
`@register_renderer`, and an optional validation rule. No page documents it yet,
and no code implements it, so this task waits on `task-1`.

## Acceptance criteria

- [ ] `docs/guides/writing-a-plugin.md` walks through a complete third-party
      node with a renderer, a POSIX decision and a validation rule.
- [ ] `docs/reference/plugins.md` documents `register_node_type`,
      `register_renderer` and the rule signature.
- [ ] The guide and `docs/reference/plugins.md` share one canonical example, and
      the README links it instead of repeating it.
- [ ] An executable example lives in `examples/` and is rendered in CI.

## Definition of done

- [ ] Documentation checks pass (`pixi run automation check-docs`, `pixi run automation lint-prose`).
- [ ] No duplicated explanation between README, concepts and reference.

## Files

- `docs/guides/writing-a-plugin.md`
- `docs/reference/plugins.md`
- `examples/` for the executable example

## Notes

Decision-1 records the strategy: one package, a backend record per target, and
the registry as the seam. The long form of that page went with the implementation
when the package was reduced to its skeleton, so this task is `To Do` until the
core engine gives the guide something to document.
