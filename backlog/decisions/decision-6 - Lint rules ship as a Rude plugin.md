---
id: decision-6
title: Lint rules ship as a Rude plugin, and the compiler owns the rest
date: 2026-11-10
status: Accepted
references: [pyshellforge-rude/pyproject.toml, pyshellforge-rude/src/pyshellforge_rude/rules.py, pyshellforge-rude/tests/test_rules.py, docs/reference/linting.md, .coveragerc]
---

## Context

A definition is Python, and the conventions that keep the generated script
readable can be checked before anything is rendered. Three candidates were on the
table.

Writing the rules into `psf validate` only would tie every editor session to the
compiler: a user who wants a warning in the editor on a badly cased name would
import the
package, build the tree and render it.

Linting the generated script with a shell linter answers a different question. It
reports on text the user never wrote, at a line number the user cannot act on,
and the findings that matter most — an unquoted expansion — are guarantees the
renderer must provide rather than defects a definition can contain.

A Python linter with a custom-rule API can read the same tree the compiler reads,
in the editor, with no import. Rude qualifies: it exposes a rule base class, a
semantic scope model and an entry-point plugin mechanism, and it is what the
sibling [`rude-clean-code`](https://github.com/Archont561/rude-clean-code)
project targets.

## Decision

Ship the source-level rules as `pyshellforge-rude`, a second distribution in this
repository, and keep every rule that needs the compiler out of it.

- The distribution registers its rules through the `rude.plugins` entry point,
  so `pip install pyshellforge-rude` is the whole setup. `pyshellforge` keeps
  `dependencies = []`; Rude is never a runtime requirement of the generator.
- The first two rules are the casing pair: `PSF201` (a module-level binding is
  `UPPER_CASE`) and `PSF202` (a function-scoped binding is `lower_case`). The case
  is the reader's only signal that a name renders as a global or as a `local`.
- Both report at warning severity. Scope is resolved by position, so the name is
  documentation and a build should not fail over it.
- Both rules run only in files that mention `pyshellforge` or `@sh`, so installing
  the plugin does not re-case the rest of a repository.
- Rude is pinned below `0.2`. A plugin is the first thing a pre-1.0 rule API
  breaks, and the rules depend on the semantic model rather than on tree shape
  alone.
- The rule codes come from the same families the validator will use (names are
  `PSF2xx`), so a convention has one code in both engines and a suppression in a
  definition keeps working when `psf validate` lands.
- No automatic fix. Renaming a binding means rewriting every reference, and the fix
  API is per node, which makes a partial rename likely and a wrong rename silent.

The work is split three ways, and a rule belongs to exactly one layer:

| Layer | Owns | Engine |
| --- | --- | --- |
| Syntax and scope | casing, banned calls, a definition that does not look like one | the Rude plugin |
| Structure and capability | unused names, duplicate functions, constructs the target cannot express, unsafe expansions | `psf validate` |
| The artifact | quoting, `set -euo pipefail`, syntax | tests over the renderer, plus `bash -n` and ShellCheck on the golden files |

## Consequences

The rules are usable today, before a renderer exists, which is why this
distribution could ship while the package is still a skeleton.

Two rule sets now have to stay aligned by hand: `PSF201` and `PSF202` are
implemented once, but any later rule that both engines could express must be
written in the validator first and mirrored only if the editor feedback is worth
the duplicate.

Anything the plugin cannot see — the target shell, declared types, whether a name
is used — stays invisible until the validator exists, so users of the plugin alone
get a partial check. `docs/reference/linting.md` says so rather than implying that
a clean Rude run means a valid definition.

Publishing needs its own release path: the current workflow publishes
`pyshellforge` from a tag that must match its manifest, and the plugin is a
separate name and version. That gap is `task-12`.
