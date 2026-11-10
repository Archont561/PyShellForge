"""Generate and maintain ``AGENTS.md`` with the ``agents-md`` CLI.

``AGENTS.md`` is the cross-tool agent-instructions standard, and it is maintained
rather than written once: the [``agents-md``](https://github.com/eugeniughelbur/agents-md)
CLI scans the repository and refreshes the sections it produced, while everything
outside its markers is preserved.

The CLI's contract is a pair of HTML comments per section::

    <!-- agents-md:begin id=commands -->
    ## Commands
    ...
    <!-- agents-md:end id=commands -->

This module owns the two halves of that contract:

``bootstrap``
    Run the pinned CLI to create the skeleton. It is a maintainer action, needs
    npm and network access, and is refused once the file carries markers, so a
    refresh cannot quietly discard the curated text between the markers.

``check``
    Verify the committed file offline: every generated section is present, in
    the CLI's order, headed as the CLI expects, filled in rather than left as a
    ``_TBD:`` stub, and not shadowed by a stale ``AGENTS.generated.md`` sidecar
    (which the CLI writes when it finds no markers at all). CI runs this.

Usage::

    python -m automation.agents --check       # offline validation (CI)
    python -m automation.agents --bootstrap   # create the skeleton with the CLI
    python -m automation.agents --bootstrap --force

The CLI version is pinned in ``package.json`` under ``devDependencies``, the same
way the README generator is pinned.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

#: Repository root, derived from this file (``automation/agents/generate.py``).
REPO_ROOT = Path(__file__).resolve().parents[2]

#: The maintained file.
TARGET = REPO_ROOT / "AGENTS.md"

#: Sidecar the CLI writes when it finds an ``AGENTS.md`` without markers.
SIDECAR = REPO_ROOT / "AGENTS.generated.md"

#: Metadata file that pins the CLI version.
PACKAGE_JSON = REPO_ROOT / "package.json"

#: npm package that provides the generator.
CLI_PACKAGE = "@eugeniughelbur/agents-md"

#: Sections the CLI generates, in the order it writes them.
SECTIONS: tuple[str, ...] = (
    "overview",
    "commands",
    "testing",
    "structure",
    "conventions",
    "git",
    "gotchas",
    "security",
    "boundaries",
)

#: Heading the CLI writes for each section id.
TITLES: dict[str, str] = {
    "overview": "Overview",
    "commands": "Commands",
    "testing": "Testing",
    "structure": "Project structure",
    "conventions": "Code style & conventions",
    "git": "Git & PR workflow",
    "gotchas": "Gotchas & hard-won lessons",
    "security": "Security & secrets",
    "boundaries": "Boundaries",
}

#: Marker the CLI leaves where it could not detect a fact.
STUB = "_TBD:"

#: Codes are stable; documentation and tests quote them.
CODES: dict[str, str] = {
    "PSF-AGENT-001": "AGENTS.md is missing",
    "PSF-AGENT-002": "generated section marker is missing",
    "PSF-AGENT-003": "generated sections are out of order",
    "PSF-AGENT-004": "generated section is empty",
    "PSF-AGENT-005": "unfinished agents-md stub is still present",
    "PSF-AGENT-006": "AGENTS.generated.md sidecar exists, so AGENTS.md lost its markers",
    "PSF-AGENT-007": "section heading does not match its marker id",
}

#: A runner executes a command in ``cwd`` and returns its exit status.
Runner = Callable[..., int]


@dataclass(frozen=True, order=True)
class Finding:
    """One defect in the maintained file."""

    path: str
    line: int
    code: str
    message: str

    def format(self) -> str:
        """Render as ``path:line: CODE message``."""
        return f"{self.path}:{self.line}: {self.code} {self.message}"

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serialisable representation."""
        return asdict(self)


def begin_marker(section: str) -> str:
    """Return the opening marker comment for ``section``."""
    return f"<!-- agents-md:begin id={section} -->"


def end_marker(section: str) -> str:
    """Return the closing marker comment for ``section``."""
    return f"<!-- agents-md:end id={section} -->"


def subprocess_runner(command: Sequence[str], *, cwd: Path) -> int:
    """Run ``command`` in ``cwd`` with inherited stdio."""
    return subprocess.run(list(command), cwd=cwd, check=False).returncode


def pinned_version(package_json: Path = PACKAGE_JSON) -> str:
    """Return the exact CLI version pinned in ``package.json``.

    Raises:
        ValueError: if the dependency is missing or not an exact pin.
    """
    data = json.loads(package_json.read_text(encoding="utf-8"))
    version = data.get("devDependencies", {}).get(CLI_PACKAGE)
    if not version:
        msg = f"{CLI_PACKAGE} is not pinned in {package_json.name}"
        raise ValueError(msg)
    if not all(part.isdigit() for part in str(version).split(".")):
        msg = f"pin {CLI_PACKAGE} to an exact version, got {version!r}"
        raise ValueError(msg)
    return str(version)


def generator_command(version: str) -> list[str]:
    """Build the ``npx`` invocation used to run the pinned CLI."""
    npx = "npx.cmd" if sys.platform == "win32" else "npx"
    return [npx, "--yes", f"{CLI_PACKAGE}@{version}", "--no-symlink"]


def section_body(text: str, section: str) -> str | None:
    """Return the text between the markers of ``section``, or ``None``.

    ``None`` means the marker pair is missing; an empty string means the pair is
    present but the section has no body.
    """
    start, end = begin_marker(section), end_marker(section)
    opening = text.find(start)
    if opening < 0:
        return None
    closing = text.find(end, opening)
    if closing < 0:
        return None
    return text[opening + len(start) : closing].strip()


def markers_in(text: str) -> list[str]:
    """Return section ids in the order their opening markers appear."""
    found: list[tuple[int, str]] = []
    for section in SECTIONS:
        index = text.find(begin_marker(section))
        if index >= 0:
            found.append((index, section))
    return [section for _, section in sorted(found)]


def _line_of(text: str, needle: str) -> int:
    index = text.find(needle)
    if index < 0:
        return 1
    return text.count("\n", 0, index) + 1


def _heading_of(body: str) -> str | None:
    for line in body.splitlines():
        if line.startswith("## "):
            return line[3:].strip()
    return None


def _stub_findings(relative: str, line: int, body: str, section: str) -> list[Finding]:
    """Report every agents-md stub the CLI left inside a section body."""
    return [
        Finding(
            relative,
            line + offset,
            "PSF-AGENT-005",
            f"fill in the agents-md stub in section {section!r} or move the fact outside the markers",
        )
        for offset, content in enumerate(body.splitlines())
        if STUB in content
    ]


def _check_section(relative: str, text: str, section: str) -> list[Finding]:
    """Check the markers, the heading and the stubs of one generated section."""
    body = section_body(text, section)
    if body is None:
        return [
            Finding(
                relative,
                1,
                "PSF-AGENT-002",
                f"generated section {section!r} is missing its markers ({begin_marker(section)})",
            )
        ]
    line = _line_of(text, begin_marker(section))
    if not body:
        return [Finding(relative, line, "PSF-AGENT-004", f"generated section {section!r} is empty")]

    findings: list[Finding] = []
    heading = _heading_of(body)
    if heading != TITLES[section]:
        findings.append(
            Finding(
                relative,
                line,
                "PSF-AGENT-007",
                f"section {section!r} must be headed {TITLES[section]!r}, found {heading!r}",
            )
        )
    findings.extend(_stub_findings(relative, line, body, section))
    return findings


def _check_structure(root: Path, relative: str, text: str) -> list[Finding]:
    """Check the marker order and the sidecar the CLI writes without markers."""
    findings: list[Finding] = []
    present = markers_in(text)
    if present and present != [section for section in SECTIONS if section in present]:
        findings.append(
            Finding(
                relative,
                1,
                "PSF-AGENT-003",
                "generated sections are not in the order agents-md writes them",
            )
        )
    if (root / SIDECAR.name).is_file():
        findings.append(
            Finding(
                SIDECAR.name,
                1,
                "PSF-AGENT-006",
                "delete the sidecar and restore the markers in AGENTS.md; the CLI writes a sidecar only when it finds no markers",
            )
        )
    return findings


def check_agents(root: Path = REPO_ROOT) -> list[Finding]:
    """Validate ``root/AGENTS.md`` against the agents-md marker contract.

    The checks are offline and deterministic: they read the committed file and
    look for the sidecar, nothing else.
    """
    root = Path(root)
    target = root / TARGET.name
    relative = TARGET.name

    if not target.is_file():
        return [
            Finding(relative, 1, "PSF-AGENT-001", "AGENTS.md must exist at the repository root")
        ]

    text = target.read_text(encoding="utf-8")
    findings: list[Finding] = []
    for section in SECTIONS:
        findings.extend(_check_section(relative, text, section))
    findings.extend(_check_structure(root, relative, text))
    return findings


def bootstrap(
    *,
    root: Path = REPO_ROOT,
    runner: Runner = subprocess_runner,
    force: bool = False,
) -> bool:
    """Create the ``AGENTS.md`` skeleton by running the pinned CLI.

    Returns ``False`` without running anything when the file already carries
    markers and ``force`` is not set, because a re-run would replace the curated
    text inside them with whatever the scanner can detect.
    """
    root = Path(root)
    target = root / TARGET.name
    if (
        target.is_file()
        and begin_marker(SECTIONS[0]) in target.read_text(encoding="utf-8")
        and not force
    ):
        return False

    command = generator_command(pinned_version(root / PACKAGE_JSON.name))
    return runner(command, cwd=root) == 0


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point: validate by default, or bootstrap with the CLI."""
    parser = argparse.ArgumentParser(
        prog="python -m automation.agents",
        description="Validate AGENTS.md against the agents-md marker contract, or bootstrap it.",
    )
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help="repository root")
    parser.add_argument("--json", action="store_true", help="emit JSON findings")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="validate the file (default)")
    mode.add_argument(
        "--bootstrap", action="store_true", help="create the skeleton with the pinned CLI"
    )
    parser.add_argument(
        "--force", action="store_true", help="allow --bootstrap to rewrite an existing file"
    )
    args = parser.parse_args(argv)

    if args.bootstrap:
        if not bootstrap(root=args.root, force=args.force):
            print(
                "agents: AGENTS.md already has markers; refusing to overwrite (pass --force to regenerate)"
            )
            return 1
        findings = check_agents(args.root)
        stubs = sum(1 for finding in findings if finding.code == "PSF-AGENT-005")
        print(f"agents: skeleton created with {CLI_PACKAGE}; {stubs} stub(s) to fill in")
        return 0

    findings = check_agents(args.root)
    if args.json:
        print(json.dumps([finding.to_dict() for finding in findings], indent=2))
    else:
        for finding in findings:
            print(finding.format())
        status = "ok" if not findings else f"{len(findings)} finding(s)"
        print(f"agents: {len(SECTIONS)} section(s), {status}")
    return 1 if findings else 0


if __name__ == "__main__":  # pragma: no cover - module entry point
    raise SystemExit(main())
