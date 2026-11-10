---
id: task-5
title: Establish the prose lint baseline
status: Done
labels: [docs, tooling]
created_date: 2026-11-09
dependencies: []
references: [.vale.ini, .vale/styles/README.md, .vale/styles/config/vocabularies/Project/accept.txt]
---

## Description

Wire Vale, markdownlint-cli2, lychee, alint and the repository's own documentation
validator into Pixi tasks, the git hooks and CI, and document the impact
assessment each change needs.

## Acceptance criteria

- [x] `.vale.ini` plus a project vocabulary, `.markdownlint-cli2.yaml`,
      `lychee.toml`, `.alint.yml` and `gherlint.toml` exist and are referenced by
      Pixi tasks.
- [x] `python -m automation.docs` validates structure, navigation, links, anchors
      and heading shape offline.
- [x] Documentation policy, including the definition of done, is documented in
      `docs/development/documentation.md`.
- [x] CI runs the documentation checks and requires them to pass.

## Notes

Keep new findings out of the tree: add legitimate terms to the vocabulary rather
than disabling rules.

## Outcome

Vale now runs the vendored Microsoft style package over every Markdown file,
including `backlog/**` (decision-2). Baseline after the cleanup: 0 errors,
17 advisory warnings.
