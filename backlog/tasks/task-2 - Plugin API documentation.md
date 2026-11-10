---
id: task-2
title: Plugin API documentation
status: In Progress
milestone: m-1
labels: [docs, plugins]
created_date: 2026-11-09
dependencies: [task-1]
references: [docs/concepts/ast-design.md, docs/architecture/multi-shell.md, src/pyshellforge/core/registry.py]
---

## Description

The plugin contract (dataclass node, `render_<snake_case>` or
`@register_renderer`, optional validation rule) exists but is only shown as a
snippet in the README and one concept page.

## Acceptance criteria

- [ ] `docs/guides/writing-a-plugin.md` walks through a complete third-party
      node with a renderer, a POSIX decision and a validation rule.
- [ ] `docs/reference/plugins.md` documents `register_node_type`,
      `register_renderer` and the rule signature.
- [ ] The README snippet and the guide share one canonical example.
- [ ] An executable example lives in `examples/` and is rendered in CI.

## Definition of done

- [ ] Documentation checks pass (`pixi run automation check-docs`, `pixi run automation lint-prose`).
- [ ] No duplicated explanation between README, concepts and reference.

## Progress

`docs/architecture/multi-shell.md` documents the plugin strategy, the per-target
capability matrix and the checklist for adding a shell (decision-1). Remaining:
a dedicated `docs/reference/plugins.md` with the worked example and the validation
hook contract.
