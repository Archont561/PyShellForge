# PyShellForge documentation

Start with the page that matches what you are doing. Every page here is checked by
`python -m automation.docs` (structure, navigation, links, anchors) and by
markdownlint-cli2, Vale and lychee in CI.

The generator lives in `packages/pyshellforge/` and is a skeleton: its single module,
`packages/pyshellforge/src/pyshellforge/__init__.py`, exposes `VERSION`, read from the
manifest beside it, and nothing renders shell yet. `packages/pyshellforge-rude/` is the
second distribution, a Rude plugin that checks the casing conventions of a
definition; it is the one thing that can be installed and used today.

## Concepts

What exists today and what is planned.

| Page | Covers |
| --- | --- |
| [Project status](concepts/version-only-scaffold.md) | The skeleton, how `VERSION` resolves, the roadmap |

## Guides

Installing, using and operating the project.

| Page | Covers |
| --- | --- |
| [Install](guides/install.md) | Prerequisites, `pip install`, the locked developer sandbox |

## Reference

| Page | Covers |
| --- | --- |
| [Repository layout](reference/repository-layout.md) | What lives where and why |
| [Linting](reference/linting.md) | The Rude plugin, its rule codes, and the rules that wait for the validator |

## Development

Working on PyShellForge itself.

| Page | Covers |
| --- | --- |
| [Contributing](development/contributing.md) | Setup, the checks CI runs, commit style, reporting bugs |
| [Testing](development/testing.md) | Test layout, what each layer proves, coverage |
| [Tooling](development/tooling.md) | The `automation` CLI, its task graph, hooks and linters |
| [Documentation](development/documentation.md) | Policy, structure, validation and definition of done |
| [Releasing](development/releasing.md) | The release workflow, trusted publishing, the tag/version guard |

## Where to start

- Setting up a checkout: [Contributing](development/contributing.md).
- Installing or using the package: [Install](guides/install.md).
- Running or extending the checks: [Tooling](development/tooling.md).
- Understanding what the suite proves: [Testing](development/testing.md).
- Writing a page: [Documentation](development/documentation.md).
- Cutting a release: [Releasing](development/releasing.md).

The roadmap for the library itself lives in
[Project status](concepts/version-only-scaffold.md), and the working material is
in [`backlog/`](../backlog/) and [`CHANGELOG.md`](../CHANGELOG.md).
