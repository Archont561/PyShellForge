"""Task registry for the repository automation.

``pixi run automation <task>`` is a thin wrapper around ``doit``, which imports
this file to discover tasks. Every task here is a name, a docstring and an
action; the automation itself lives in ``automation/`` and knows nothing about
doit. Nothing in this module runs at import time, because importing it is how
doit learns what exists.

The rules this registry follows:

* **Doit owns the graph, the modules own the work.** A task names a ``main()``
  or a command; it never implements the command.
* **Names are kebab-case.** doit derives a task name from its ``task_``
  function, so every task also sets ``basename``; that keeps the CLI identical
  to the names this repository documented before (`check-docs`, `test-all`).
* **No artificial caching.** Linting, testing, publishing and anything else that
  touches the outside world runs every time it is asked for. ``file_dep`` and
  ``targets`` are deliberately absent, so doit can never skip a release upload
  because a target looked fresh.
* **The gate is a task, not a shell loop.** ``check`` has no actions of its own:
  it declares the checks as dependencies, so ``doit check`` orders them and
  ``doit -n 4 check`` runs the independent ones in parallel.

Usage::

    pixi run automation list              # discover every task
    pixi run automation check             # the aggregate gate
    pixi run automation test-all          # product suite and automation suite
    pixi run automation release-build --ref v0.1.0
    pixi run automation -n 4 check        # parallel gates

Modules remain runnable without doit: ``python -m automation.docs`` and
``pixi run automation check-docs`` do the same thing.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

from automation import agents, docs, forms, gherkin, readme, release

#: Defaults for every invocation of ``doit`` in this repository.
DOIT_CONFIG = {
    # `pixi run automation` with no task prints what is available instead of
    # running something expensive by surprise.
    "default_tasks": ["list"],
    "verbosity": 2,
}

#: The distribution lives in its own project directory.
PYTEST = "python -m pytest -c packages/pyshellforge/pyproject.toml"
TOX = "python -m tox -c packages/pyshellforge/tox.ini"

#: The checks `check` depends on, in the order the report reads best.
GATES: tuple[str, ...] = (
    "lint",
    "format-check",
    "typecheck",
    "check-docs",
    "lint-features",
    "check-forms",
    "readme-check",
    "agents-check",
    "alint",
    "actionlint",
    "lint-markdown",
    "lint-prose",
    "lint-links",
    "check-release",
)

#: Automation ``main`` functions return an exit status; doit wants an exception.
Action = Callable[..., None]


def _run(main: Callable[[Sequence[str] | None], int], argv: Sequence[str] | None = None) -> Action:
    """Adapt an automation ``main(argv)`` (0 means success) into a doit action."""

    def action() -> None:
        status = main(list(argv) if argv is not None else [])
        if status:
            raise RuntimeError(f"task failed with exit status {status}")

    return action


# -- gates: Python automation ------------------------------------------------
def task_check_docs() -> dict[str, object]:
    """Validate docs/: structure, navigation, links, anchors, code fences."""
    return {"basename": "check-docs", "actions": [_run(docs.main)]}


def task_lint_features() -> dict[str, object]:
    """Lint the Gherkin files and cross-check every step with its definition."""
    return {"basename": "lint-features", "actions": [_run(gherkin.main)]}


def task_lint_features_gherlint() -> dict[str, object]:
    """Gherkin style with gherlint, which lives in its own Pixi environment."""
    return {
        "basename": "lint-features-gherlint",
        "actions": [
            "pixi run --locked --environment gherkin -- python -m gherlint lint automation/features"
        ],
    }


def task_check_forms() -> dict[str, object]:
    """Validate the GitHub Issue Forms against GitHub's schema."""
    return {"basename": "check-forms", "actions": [_run(forms.main)]}


def task_readme() -> dict[str, object]:
    """Regenerate README.md and packages/pyshellforge/README.md from README.ejs."""
    return {"basename": "readme", "actions": [_run(readme.main)]}


def task_readme_check() -> dict[str, object]:
    """Fail when either generated README is stale."""
    return {"basename": "readme-check", "actions": [_run(readme.main, ["--check"])]}


def task_agents() -> dict[str, object]:
    """Regenerate the marked sections of AGENTS.md with the pinned CLI."""
    return {"basename": "agents", "actions": [_run(agents.main, ["--bootstrap"])]}


def task_agents_check() -> dict[str, object]:
    """Enforce the agents-md marker contract in AGENTS.md, offline."""
    return {"basename": "agents-check", "actions": [_run(agents.main, ["--check"])]}


def task_check_release() -> dict[str, object]:
    """Compare the tag with [project].version and build nothing."""
    return {"basename": "check-release", "actions": [_run(release.main, ["--check"])]}


# -- gates: commands the environment owns -----------------------------------
def task_lint() -> dict[str, object]:
    """Ruff lint over the repository."""
    return {"basename": "lint", "actions": ["ruff check ."]}


def task_format() -> dict[str, object]:
    """Ruff format: rewrite what it can."""
    return {"basename": "format", "actions": ["ruff format ."]}


def task_format_check() -> dict[str, object]:
    """Ruff format in check mode."""
    return {"basename": "format-check", "actions": ["ruff format --check ."]}


def task_typecheck() -> dict[str, object]:
    """mypy, strict, against the project's configuration file."""
    return {
        "basename": "typecheck",
        "actions": ["mypy --config-file packages/pyshellforge/pyproject.toml"],
    }


def task_alint() -> dict[str, object]:
    """Repository conventions and required files."""
    return {"basename": "alint", "actions": ["alint check"]}


def task_actionlint() -> dict[str, object]:
    """Lint the GitHub Actions workflows."""
    return {"basename": "actionlint", "actions": ["actionlint .github/workflows/*.yml"]}


def task_lint_markdown() -> dict[str, object]:
    """markdownlint-cli2 over every Markdown file."""
    return {"basename": "lint-markdown", "actions": ['npx --yes markdownlint-cli2 "**/*.md"']}


def task_lint_prose() -> dict[str, object]:
    """Vale with the vendored Microsoft style."""
    return {
        "basename": "lint-prose",
        "actions": [
            "vale --config .vale.ini --no-global README.md AGENTS.md CONTRIBUTING.md "
            "CHANGELOG.md docs packages/pyshellforge/README.md automation/features backlog"
        ],
    }


def task_lint_links() -> dict[str, object]:
    """lychee: external URLs and in-repo link targets."""
    return {"basename": "lint-links", "actions": ["lychee --config lychee.toml ."]}


def task_update_prose_styles() -> dict[str, object]:
    """Refresh the vendored Vale style packages."""
    return {"basename": "update-prose-styles", "actions": ["vale sync"]}


def task_lint_commit() -> dict[str, object]:
    """convco: conventional-commit format, read from stdin."""
    return {"basename": "lint-commit", "actions": ["convco check --from-stdin --strip"]}


def task_hooks_install() -> dict[str, object]:
    """Install the Lefthook git hooks."""
    return {"basename": "hooks-install", "actions": ["lefthook install"]}


# -- tests ------------------------------------------------------------------
def task_test() -> dict[str, object]:
    """The product suite."""
    return {"basename": "test", "actions": [f"{PYTEST} packages/pyshellforge/tests"]}


def task_test_automation() -> dict[str, object]:
    """The automation suite."""
    return {"basename": "test-automation", "actions": [f"{PYTEST} automation/tests"]}


def task_test_all() -> dict[str, object]:
    """Both suites."""
    return {
        "basename": "test-all",
        "actions": [f"{PYTEST} packages/pyshellforge/tests automation/tests"],
    }


def task_coverage() -> dict[str, object]:
    """Coverage for the product suite, with the repository's gate."""
    return {
        "basename": "coverage",
        "actions": [
            f"{PYTEST} packages/pyshellforge/tests --cov --cov-report=term-missing "
            "--cov-report=xml:coverage.xml"
        ],
    }


def task_coverage_all() -> dict[str, object]:
    """Coverage for both suites: the configuration CI gates on."""
    return {
        "basename": "coverage-all",
        "actions": [
            f"{PYTEST} packages/pyshellforge/tests automation/tests --cov --cov-report=term-missing "
            "--cov-report=xml:coverage.xml"
        ],
    }


def task_properties() -> dict[str, object]:
    """The product suite without the integration tests."""
    return {
        "basename": "properties",
        "actions": [f"{PYTEST} packages/pyshellforge/tests -m 'not integration' -q"],
    }


def task_test_matrix() -> dict[str, object]:
    """Every interpreter installed locally, each in its own virtualenv."""
    return {"basename": "test-matrix", "actions": [TOX]}


def task_test_matrix_one() -> dict[str, object]:
    """The tox environment matching the current interpreter."""
    return {"basename": "test-matrix-one", "actions": [f"{TOX} -e py"]}


def task_coverage_merge() -> dict[str, object]:
    """Merge the per-interpreter tox coverage data and enforce the gate."""
    return {"basename": "coverage-merge", "actions": [f"{TOX} -e coverage"]}


# -- packaging and release --------------------------------------------------
def task_build() -> dict[str, object]:
    """Build the sdist and the wheel into dist/."""
    return {
        "basename": "build",
        "actions": ["python -m build --outdir dist packages/pyshellforge"],
    }


def task_check_packages() -> dict[str, object]:
    """twine check over the built distributions."""
    return {"basename": "check-packages", "actions": ["python -m twine check dist/*"]}


def task_release_build() -> dict[str, object]:
    """Guard the tag, empty dist/, build and twine-check the release."""
    return {
        "basename": "release-build",
        "actions": [_release_build],
        "params": [
            {
                "name": "ref",
                "long": "ref",
                "short": "r",
                "default": "",
                "type": str,
                "help": "tag to compare with [project].version (default: $GITHUB_REF_NAME)",
            },
            {
                "name": "skip_tag_check",
                "long": "skip-tag-check",
                "default": False,
                "type": bool,
                "help": "build without comparing the tag",
            },
        ],
    }


def _release_build(ref: str = "", skip_tag_check: bool = False) -> None:
    """Run the release build with the parameters doit collected."""
    argv: list[str] = []
    if ref:
        argv += ["--ref", ref]
    if skip_tag_check:
        argv += ["--skip-tag-check"]
    status = release.main(argv)
    if status:
        raise RuntimeError(f"task failed with exit status {status}")


# -- continuous integration -------------------------------------------------
def task_detect_changes() -> dict[str, object]:
    """Classify changed files into the CI suites they require."""
    return {
        "basename": "detect-changes",
        "actions": [
            "python -m automation.detect_changes --base %(base)s --head %(head)s --event %(event)s"
        ],
        "params": [
            {"name": "base", "long": "base", "default": "", "type": str, "help": "base commit"},
            {"name": "head", "long": "head", "default": "", "type": str, "help": "head commit"},
            {
                "name": "event",
                "long": "event",
                "default": "push",
                "type": str,
                "help": "GitHub event name",
            },
        ],
    }


# -- the aggregate ----------------------------------------------------------
def task_check() -> dict[str, object]:
    """Every repository check: no actions, one dependency graph."""
    return {"basename": "check", "actions": [], "task_dep": list(GATES)}
