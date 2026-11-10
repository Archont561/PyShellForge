"""Run the Clean Code rules over the repository's own Python.

``rude`` is a linter with a plugin system; ``rude-clean-code`` ships the
deterministic size, parameter, scope and complexity rules (``CC101``-``CC303``)
through it. This module is the gate: it calls ``python -m rude`` with the
repository configuration and the same trees mypy checks, and turns the findings
into the exit status ``doit`` and CI need.

The wrapper exists because ``rude`` reports those rules as warnings and exits
``0`` when it finds only warnings, and because the configuration lives in
``packages/pyshellforge/pyproject.toml`` rather than at the repository root,
which is where ``rude`` looks for a ``pyproject.toml``. Passing ``--config``
explicitly is what keeps a bare ``rude check`` from applying a different rule
set than the gate.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

#: Repository root, derived from this file (``automation/clean_code/check.py``).
REPO_ROOT = Path(__file__).resolve().parents[2]

#: The manifest that carries the ``[tool.rude]`` table.
CONFIG = REPO_ROOT / "packages" / "pyshellforge" / "pyproject.toml"

#: The trees the gate covers: the two distributions and the repository automation.
SOURCES: tuple[str, ...] = (
    "packages/pyshellforge/src",
    "packages/pyshellforge-rude/src",
    "automation",
    "dodo.py",
)

#: A runner executes a command in the repository root and returns its output.
Runner = Callable[[Sequence[str]], str]


@dataclass(frozen=True, order=True)
class Finding:
    """One diagnostic ``rude`` reported."""

    path: str
    line: int
    column: int
    code: str
    message: str

    def format(self) -> str:
        """Return the finding as ``path:line:column: CODE message``."""
        return f"{self.path}:{self.line}:{self.column}: {self.code} {self.message}"

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serialisable representation."""
        return {
            "path": self.path,
            "line": self.line,
            "column": self.column,
            "code": self.code,
            "message": self.message,
        }


def subprocess_runner(command: Sequence[str]) -> str:
    """Run ``command`` and return its stdout, raising when the tool itself fails."""
    completed = subprocess.run(
        list(command),
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        msg = f"rude exited with status {completed.returncode}: {detail}"
        raise RuntimeError(msg)
    if completed.stderr.strip():
        raise RuntimeError(f"rude reported a tool warning: {completed.stderr.strip()}")
    return completed.stdout


def rude_command(paths: Sequence[str], config: Path = CONFIG) -> list[str]:
    """Build the ``rude check`` invocation the gate uses."""
    return [
        sys.executable,
        "-m",
        "rude",
        "check",
        "--format",
        "json",
        "--config",
        str(config),
        *paths,
    ]


def parse_findings(output: str) -> list[Finding]:
    """Parse JSON-lines output, rejecting unexpected output rather than passing silently."""
    findings: list[Finding] = []
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
            item = Finding(
                path=str(record["file"]),
                line=int(record["line"]),
                column=int(record["column"]),
                code=str(record["code"]),
                message=str(record["message"]),
            )
        except (ValueError, TypeError, KeyError) as error:
            raise RuntimeError(f"invalid rude JSON output: {line}") from error
        findings.append(item)
    return sorted(set(findings))


def check_repository(
    paths: Sequence[str] = SOURCES,
    *,
    config: Path = CONFIG,
    runner: Runner = subprocess_runner,
) -> list[Finding]:
    """Run the Clean Code rules over ``paths`` and return every finding.

    Args:
        paths: the files and directories to check.
        config: the manifest holding the ``[tool.rude]`` table.
        runner: executes the command; injectable so the tests never race a linter.

    Returns:
        The findings, sorted and without duplicates.

    Raises:
        RuntimeError: if ``rude`` cannot run or exits with a tool failure.
    """
    return parse_findings(runner(rude_command(paths, config)))


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point: print the findings, exit 1 when there are any.

    Returns:
        0 when the trees are clean, 1 when there are findings, 2 when the linter
        itself failed.
    """
    parser = argparse.ArgumentParser(
        prog="python -m automation.clean_code",
        description="Run the rude Clean Code rules over the repository's Python.",
    )
    parser.add_argument("paths", nargs="*", default=list(SOURCES), help="files or directories")
    parser.add_argument("--config", type=Path, default=CONFIG, help="manifest with [tool.rude]")
    parser.add_argument("--json", action="store_true", help="emit JSON findings")
    args = parser.parse_args(argv)

    if not args.config.is_file():
        print(f"clean-code: config file not found: {args.config}", file=sys.stderr)
        return 2

    try:
        findings = check_repository(args.paths, config=args.config)
    except RuntimeError as error:
        print(f"clean-code: {error}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps([finding.to_dict() for finding in findings], indent=2))
    else:
        for finding in findings:
            print(finding.format())
        status = "ok" if not findings else f"{len(findings)} finding(s)"
        print(f"clean-code: {len(args.paths)} path(s), {status}")
    if findings and not args.json:
        print(
            f"codes: {', '.join(sorted({finding.code for finding in findings}))}",
            file=sys.stderr,
        )
    return 1 if findings else 0
