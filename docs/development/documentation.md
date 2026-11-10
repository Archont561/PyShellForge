# Documentation

The `docs/` directory is the primary user-facing knowledge layer of this
repository. It is the maintained, discoverable source of truth for understanding,
using, configuring and operating PyShellForge, and it serves both human readers
and AI agents.

## Purpose

Documentation must be accurate, actionable, easy to navigate, and consistent with
the implementation. It is part of the product, not a summary of it.

## Principles

1. **Documentation is part of the product.** It is not an afterthought.
2. **Prefer one canonical explanation.** Never duplicate the same knowledge in
   two places; link to the canonical page instead.
3. **Document observable behaviour.** Describe what the software does, not what
   was intended.
4. **Write for users first.** Practical explanations, examples and instructions
   beat implementation-centric descriptions.
5. **Keep it discoverable.** Organize by purpose and keep navigation current.
6. **Treat outdated documentation as a defect.** Fix incorrect instructions and
   obsolete references immediately.

## Structure

The tree follows purpose, and it holds only the sections that have content:

| Directory | Purpose |
| --- | --- |
| [`concepts/`](../concepts/) | What the project is, what exists today and what is planned |
| [`guides/`](../guides/) | Installing, using and operating the project |
| [`reference/`](../reference/) | Where things live, and why |
| [`development/`](../development/) | Contribution, testing, tooling and documentation policy |

`architecture/` comes back with the code that it would document. A page that
describes behaviour with no implementation is a defect, so the tree stays
smaller than the repository's ambitions.

`python -m automation.docs` enforces the list from the other side: it reads the
required sections from its own configuration, so a section the check requires
cannot disappear unnoticed, and a section that is added to the tree is added to
the list in the same change. Every required section must also hold at least one
page.

[`docs/README.md`](../README.md) is the navigation index: **every page must be
linked from it**, which is how pages stay discoverable and how orphans are
caught. The root `README.md` introduces the project and points here.

## Agent instructions

`AGENTS.md` is the repository's instruction file for AI agents. It is maintained
with the [`agents-md`](https://github.com/eugeniughelbur/agents-md) CLI, whose
markers delimit the sections the CLI refreshes:

```text
<!-- agents-md:begin id=commands -->
## Commands
...
<!-- agents-md:end id=commands -->
```

Everything inside a marker pair belongs to the CLI; everything outside, including
the `## Notes` section, is hand-owned and preserved. In this repository the marked
sections are curated rather than left as a raw scan, because the CLI reads npm and
Python manifests while the real commands live in `pixi.toml` and
`packages/pyshellforge/tox.ini`.
`python -m automation.agents --check` enforces the contract: all nine sections
present and in order, headed as the CLI expects, no unfinished stub, and no stale
`AGENTS.generated.md` sidecar. It runs in the pre-commit hook and in CI, so a
refresh or a hand edit cannot quietly break the file.

`AGENTS.md` is not a `docs/` page and is not part of the navigation index; treat
it as an entry point that points at `docs/` for depth.

## Preventing drift

Documentation evolves with the software. Every change that affects user-visible
behaviour, configuration, APIs, workflows or operational requirements must
include a documentation impact assessment. During implementation and review:

1. Identify the affected documentation.
2. Update the canonical page instead of adding a duplicate.
3. Add documentation for new user-facing capability.
4. Remove obsolete instructions, examples and references.
5. Verify that commands, configuration examples and code snippets still work.
6. Verify that internal links and navigation resolve.

A change is not fully documented because the implementation is complete.

## Validation

Documentation quality is maintained by automated checks plus human review.

| Layer | Tool | Command |
| --- | --- | --- |
| Structure, navigation, internal links, anchors | `automation.docs` | `pixi run automation check-docs` |
| Markdown formatting and consistency | markdownlint-cli2 | `pixi run automation lint-markdown` |
| Writing style, terminology, language | Vale + Microsoft style | `pixi run automation lint-prose` |
| Broken links and references | lychee | `pixi run automation lint-links` |
| Repository conventions | alint | `pixi run automation alint` |

All of them run in CI and must pass before merging. Vale lints against the
vendored Microsoft style package (`.vale/styles/Microsoft`, refreshed with
`pixi run automation update-prose-styles`): errors fail the check, warnings are advisory
and must still be reviewed. Three Microsoft rules are disabled with a written
justification in `.vale.ini` (contractions, the backend entry of the A-Z word
list, and acronyms in headings) because reference documentation needs a neutral
voice, the domain term, and API names such as `CLI` and `AST`. Add legitimate project terms to
`.vale/styles/config/vocabularies/Project/accept.txt` rather than disabling rules.

Automated checks are necessary but insufficient: reviewers must also judge whether
the documentation describes the implemented behaviour.

## Definition of done

A change that affects documentation satisfies all of the following:

- Relevant documentation has been identified.
- Existing documentation has been updated where necessary.
- New user-facing behaviour is documented.
- Examples and instructions reflect the current implementation.
- Obsolete information has been removed.
- Documentation validation passes.

If no documentation change is necessary, that decision is stated explicitly in the
pull request.

## Ownership

Every contributor who changes the product owns its documentation impact.
Documentation is maintained continuously as part of normal development, not
deferred to periodic cleanups. The goal is for `docs/` to remain a trustworthy
representation of the software at all times.

## Next

- [Contributing](contributing.md) for the review checklist.
- [Tooling](tooling.md) for the tasks that run these checks.
