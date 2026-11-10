# PyShellForge documentation

Start with the page that matches what you are doing. Every page here is checked by
`python -m automation.docs` (structure, navigation, links, anchors) and by
markdownlint-cli2, Vale and lychee in CI.

The distribution lives in `pyshellforge/` and is a skeleton: its single module,
`pyshellforge/src/pyshellforge/__init__.py`, exposes `VERSION`, read from the
manifest beside it, and nothing renders shell yet. There is no user guide, no API
reference and no CLI to document, so this tree holds the development pages that
describe the repository itself.

## Development—working on PyShellForge

| Page | Covers |
| --- | --- |
| [Contributing](development/contributing.md) | Setup, the checks CI runs, commit style, reporting bugs |
| [Testing](development/testing.md) | Test layout, what each layer proves, coverage |
| [Tooling](development/tooling.md) | The `automation` CLI, its task graph, hooks and linters |
| [Documentation](development/documentation.md) | Policy, structure, validation and definition of done |
| [Releasing](development/releasing.md) | The release workflow, trusted publishing, the tag/version guard |

## Where to start

- Setting up a checkout: [Contributing](development/contributing.md).
- Running or extending the checks: [Tooling](development/tooling.md).
- Understanding what the suite proves: [Testing](development/testing.md).
- Writing a page: [Documentation](development/documentation.md).
- Cutting a release: [Releasing](development/releasing.md).

The roadmap for the library itself lives in [`backlog/`](../backlog/) and in
[`CHANGELOG.md`](../CHANGELOG.md).
