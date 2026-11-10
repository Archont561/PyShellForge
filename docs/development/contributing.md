# Contributing

## Ground rules

1. **The README states what exists.** The package is a skeleton; nothing here may
   describe a renderer, a node or a CLI that has no code behind it.
2. **One source of truth for the version.** `VERSION` is read from
   `[project].version` in `packages/pyshellforge/pyproject.toml`; never hard-code a second
   copy.
3. **Nothing executes at import time** beyond reading that version.
4. **Every change passes `pixi run automation check` and
   `pixi run automation test-all`.** Both are the same commands CI and the git
   hooks run.

## Setup

```sh
git clone https://github.com/Archont561/PyShellForge
cd PyShellForge
command -v pixi || python -m automation.restore   # Pixi, the env, the hooks
pixi run install-hooks                           # Lefthook git hooks
```

`python -m automation.restore` installs Pixi when it is missing, solves the
environment with `pixi install --locked`, and installs the Lefthook hooks. It is
the one command that does not assume Pixi exists, which is why it runs as plain
`python -m automation.restore` rather than as a task.
`python -m automation.restore --check` reports the state and exits non-zero when
something is missing.

Plain pip works too: `python -m venv .venv && . .venv/bin/activate`,
`pip install -e "packages/pyshellforge[dev]"`, then
`python -m pytest -c packages/pyshellforge/pyproject.toml packages/pyshellforge/tests automation/tests`.
The distribution is the `packages/pyshellforge/` project directory, so the manifest path is
part of every install and every pytest invocation.

## The checks CI runs

```sh
pixi run automation check       # every check, as one doit dependency graph
pixi run automation -n 4 check  # the same graph, four tasks at a time
pixi run automation test-all    # tests and the coverage gate
```

`pixi run automation list` prints every task with its docstring, so nobody has to
remember what exists.

`pixi run automation check` is the documentation and policy gate:

* `python -m automation.docs` for the `docs/` tree,
* `python -m automation.gherkin` for the Gherkin files and their step definitions,
* `python -m automation.forms` for the GitHub Issue Forms,
* `python -m automation.readme --check` and `python -m automation.agents --check`,
* alint, markdownlint-cli2, Vale and lychee.

The suite itself is small, because the product is small:
`packages/pyshellforge/tests/unit/test_version.py` covers `VERSION` and its resolution
order, and `packages/pyshellforge/tests/integration/test_readme.py`
covers the README that the generator produces.

## Regenerating the README

`README.md` is generated—do not edit it by hand. The source is
[`automation/readme/README.ejs`](../../automation/readme/README.ejs), driven by
[readme-md-generator](https://github.com/kefranabg/readme-md-generator), which
takes its metadata from [`package.json`](../../package.json).

```sh
pixi run automation readme          # rewrite README.md (npx, no npm install needed)
pixi run automation readme-check    # exit 1 if README.md is stale; CI runs this
```

The banner is generated too: the template marks where it belongs and
[`automation.banner`](../../automation/banner/render.py) draws the project name in
FIGlet art with pyfiglet, so regenerating rewrites the art and the freshness check
catches a font change.

`packages/pyshellforge/tests/integration/test_readme.py` fails if the version badge, the
prerequisites, the author or the license disagree with the manifest or
`package.json`, if a
table-of-contents link has no heading, if a relative link points at a file that
does not exist, if unrendered EJS leaked into the output, or if the README
documents something the package cannot back.

## Maintaining AGENTS.md

`AGENTS.md` is maintained with the `agents-md` CLI. Its marked sections are the
CLI's territory; the prose outside them, including `## Notes`, is yours.

```sh
pixi run automation agents          # run the pinned CLI (needs Node.js)
pixi run automation agents-check    # validate the marker contract offline; CI runs this
```

Edit facts inside the markers by hand when the scanner cannot detect them, which
in this repository is most of them, and never leave a `_TBD:` stub: the check
fails on it. If a marker pair disappears, restore it instead of deleting the
section, and delete any `AGENTS.generated.md` sidecar the CLI leaves behind.

## Adding behaviour

The order that keeps the repository honest:

1. Write the code, with types and a docstring that explains why it exists.
2. Test it: a unit test for the logic, and an execution test when only a real
   process can prove the behaviour.
3. Document it: update the canonical `docs/` page, or add one and link it from
   `docs/README.md`.
4. Add a Gherkin scenario in `automation/features/` when the change is
   user-visible, plus the step definition in `automation/tests/bdd/`, and add it to
   the module list that `automation/tests/bdd/conftest.py` imports.
5. Record the change in `CHANGELOG.md` under `Unreleased`.

## Coding style

* Python 3.11+, `from __future__ import annotations` everywhere.
* Ruff line length 100, `ruff format` formatting, import sorting via ruff.
* Full type annotations; `mypy` runs with `disallow_untyped_defs`.
* Docstrings explain *why*; the code explains *how*.
* Prefer extending an existing module over adding a new one.

## Commit messages

Conventional Commits, checked by `convco` in a commit-msg hook and in CI:

```text
feat(version): read VERSION from packages/pyshellforge/pyproject.toml
fix(docs): repoint the navigation index after a move
chore(deps): bump vale to 3.26
```

Keep the subject under 72 characters, write it in the imperative, and use the body
for why the change was needed.

## Merging

Merge a pull request with rebase, so `main` stays linear and every commit that
lands on it is one the review saw:

```sh
gh pr merge --rebase <number>
```

A merge commit does not get through. GitHub writes
`Merge pull request #123 from <branch>`, which is not a Conventional Commit, and
the `Reject merge commits on main` step fails a push that adds one. A squash
merge is not used either: it collapses a reviewed series into one commit and
loses the per-commit bodies the changelog is assembled from.

The GitHub setting *Require linear history* on `main` enforces the same rule
where GitHub can, and the CI step is the half that is visible in the log.
`convco` therefore runs without `--merges`: the check covers the commits a
contributor writes, not the merge subject GitHub may generate.

## Releasing

Publishing is a maintainer action and happens on a tag. The workflow, the guard and
the local dry run are described in [Releasing](releasing.md).

```sh
pixi run automation check-release    # the tag/version guard only
pixi run automation release-build    # guard, build, twine check; uploads nothing
```

## Reporting bugs

Bugs and feature requests go through GitHub Issue Forms, which ask for the fields
a maintainer needs before the first reply. Empty issues are disabled on purpose,
so use one of the forms or the contact links in
[`.github/ISSUE_TEMPLATE/`](../../.github/ISSUE_TEMPLATE/).

The forms are YAML, and GitHub fails quietly on a mistyped element, so the
repository checks them offline:

```bash
pixi run automation check-forms    # python -m automation.forms; part of `pixi run automation check`
```

To see a form the way a contributor will, render it locally with the
[`gh-form`](https://github.com/yudai-nkt/gh-form) extension of the GitHub CLI.
This needs `gh`, an authenticated session and network access, so it is never part
of CI:

```bash
gh extension install yudai-nkt/gh-form   # or: cargo install gh-form
gh form preview                          # from the repository root
```

`gh form preview` renders the YAML Issue Forms only. Markdown issue templates and
pull request templates are not supported, and nothing is uploaded: the preview is
local.

Include in a report:

* the PyShellForge version, from
  `python -c "import pyshellforge; print(pyshellforge.VERSION)"`,
* `python -V` and your operating system,
* what you ran, what you expected and what you got.

## Security

If a report could expose untrusted text to a shell, that is a security bug: open a
private security advisory rather than a public issue.

## Code of conduct

Be decent. Assume good faith. Critique code, not people.
