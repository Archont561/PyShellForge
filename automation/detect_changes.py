"""Decide which CI suites a change needs.

Continuous integration runs the full suite for anything that can affect the
product, but a documentation-only or automation-only change does not need to build
wheels on three operating systems. This module classifies the files touched by a
push or pull request and reports which suites are relevant.

Usage::

    python -m automation.detect_changes --base BASE_SHA --head HEAD_SHA --event push
    python -m automation.detect_changes --base ... --head ... --event pull_request --github-output

The CI workflow calls it with plain ``python`` before any environment exists, and
``pixi run automation detect-changes`` exposes the same module through doit.

Exit status is 0 even when nothing matches: the caller reads the outputs.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

#: Trees that only carry documentation or prose.
DOC_PREFIXES: tuple[str, ...] = ("docs/", "backlog/")

#: GitHub Issue Forms are checked by `python -m automation.forms`, not by the
#: packaging or interpreter matrix.
ISSUE_FORM_PREFIX = ".github/ISSUE_TEMPLATE/"

#: Trees that only carry repository automation.
AUTOMATION_PREFIXES: tuple[str, ...] = ("automation/",)

#: Individual files that affect documentation checks only.
DOC_FILES: frozenset[str] = frozenset(
    {
        ".alint.yml",
        ".markdownlint-cli2.yaml",
        ".vale.ini",
        "AGENTS.md",
        "CHANGELOG.md",
        "CONTRIBUTING.md",
        "README.md",
        "gherlint.toml",
        "lychee.toml",
    }
)

#: Marker git uses when there is no meaningful "before" commit.
NULL_SHA_PREFIX = "0000000"

GitRunner = Callable[[Sequence[str]], str]


@dataclass(frozen=True)
class Scope:
    """Which CI suites are required."""

    docs: bool
    automation: bool
    full: bool
    reason: str

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serialisable representation."""
        return asdict(self)

    def as_outputs(self) -> dict[str, str]:
        """Return GitHub Actions step outputs."""
        return {
            "run_docs": str(self.docs).lower(),
            "run_automation": str(self.automation).lower(),
            "run_full": str(self.full).lower(),
            "scope": self.reason,
        }


def git_runner(command: Sequence[str]) -> str:
    """Run a git command and return stdout."""
    return subprocess.run(
        list(command), cwd=REPO_ROOT, check=True, capture_output=True, text=True
    ).stdout


def changed_files(base: str, head: str, *, runner: GitRunner = git_runner) -> list[str]:
    """Return files changed between ``base`` and ``head``."""
    output = runner(["git", "diff", "--name-only", base, head])
    return [line.strip() for line in output.splitlines() if line.strip()]


def classify(paths: Sequence[str], *, event: str = "push") -> Scope:
    """Classify changed ``paths`` into the suites they require."""
    if event in {"workflow_dispatch", "schedule"}:
        return Scope(docs=True, automation=True, full=True, reason="manual-or-scheduled")

    if not paths:
        return Scope(docs=True, automation=True, full=True, reason="no-diff")

    docs = False
    automation_scope = False
    for path in paths:
        if (
            path in DOC_FILES
            or path.startswith((*DOC_PREFIXES, ISSUE_FORM_PREFIX))
            or path.endswith(".md")
        ):
            docs = True
        elif path.startswith(AUTOMATION_PREFIXES):
            automation_scope = True
        else:
            return Scope(docs=True, automation=True, full=True, reason=f"product:{path}")

    if docs and not automation_scope:
        reason = "docs"
    elif automation_scope and not docs:
        reason = "automation"
    else:
        reason = "docs+automation"
    return Scope(docs=docs, automation=automation_scope, full=False, reason=reason)


def resolve_scope(*, base: str, head: str, event: str, runner: GitRunner = git_runner) -> Scope:
    """Resolve the CI scope, falling back to the full suite when git cannot help."""
    if event in {"workflow_dispatch", "schedule"} or not base or base.startswith(NULL_SHA_PREFIX):
        return Scope(docs=True, automation=True, full=True, reason="manual-or-initial")
    return classify(changed_files(base, head, runner=runner), event=event)


def write_github_output(values: dict[str, str], path: str | None = None) -> None:
    """Append step outputs to ``$GITHUB_OUTPUT`` (no-op when unset)."""
    destination = path or os.environ.get("GITHUB_OUTPUT")
    if not destination:
        return
    with Path(destination).open("a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="python -m automation.detect_changes",
        description="Classify changed files into the CI suites they require.",
    )
    parser.add_argument("--base", default="", help="base commit SHA")
    parser.add_argument("--head", default="", help="head commit SHA")
    parser.add_argument("--event", default="push", help="GitHub event name")
    parser.add_argument("--github-output", action="store_true", help="write to $GITHUB_OUTPUT")
    parser.add_argument("--json", action="store_true", help="emit the scope as JSON")
    args = parser.parse_args(argv)

    try:
        scope = resolve_scope(base=args.base, head=args.head, event=args.event)
    except subprocess.CalledProcessError as error:
        print(f"warning: git diff failed ({error}); running the full suite", file=sys.stderr)
        scope = Scope(docs=True, automation=True, full=True, reason="git-error")

    if args.github_output:
        write_github_output(scope.as_outputs())
    if args.json:
        print(json.dumps(scope.to_dict(), indent=2))
    else:
        for key, value in scope.as_outputs().items():
            print(f"{key}={value}")
    return 0


if __name__ == "__main__":  # pragma: no cover - module entry point
    raise SystemExit(main())
