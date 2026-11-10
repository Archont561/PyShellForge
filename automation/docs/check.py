"""Validate the documentation tree.

The documentation in ``docs/`` is user-facing product documentation, so it is
checked the same way code is. This script is the repository's own validator: it
runs offline, on any platform, with no external binaries, and it is covered by
``automation/tests/`` and by the scenario in ``automation/features/docs_validation.feature``.

It complements the third-party tools configured in the repository:

===========================  ==========================================
Tool                         Layer
===========================  ==========================================
this script (``automation.docs``)  structure, navigation, links, anchors
``markdownlint-cli2``        Markdown formatting and consistency
``Vale`` (``lint-prose``)    spelling, terminology, editorial rules
``lychee``                   external and internal link checking
``alint``                    repository conventions
===========================  ==========================================

Usage::

    python -m automation.docs            # human-readable findings, non-zero on error
    python -m automation.docs --json     # machine-readable findings
"""

from __future__ import annotations

import argparse
import json
import re
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

#: Purpose-based documentation layout. Every directory must exist and hold pages.
REQUIRED_SECTIONS: tuple[str, ...] = ("development",)

#: Every documentation set needs a navigation index.
INDEX_NAME = "README.md"

#: Files that are documentation but not part of the navigable tree.
NAV_IGNORED: frozenset[str] = frozenset({INDEX_NAME})

FENCE = re.compile(r"^```(?P<info>[\w+-]*)")
HEADING = re.compile(r"^(?P<marks>#{1,6})\s+(?P<text>.*?)\s*$")
LINK = re.compile(r"(?<!!)\[[^\]]*\]\((?P<target>[^)\s]+)(?:\s+\"[^\"]*\")?\)")
TEMPLATE_ARTIFACT = re.compile(r"<%|%>|&#\d+;")

#: Codes are stable; documentation refers to them in ``docs/development/documentation.md``.
CODES: dict[str, str] = {
    "PSF-DOC-001": "required documentation directory is missing",
    "PSF-DOC-002": "documentation index is missing",
    "PSF-DOC-003": "documentation page is not reachable from the index",
    "PSF-DOC-004": "relative link points at a missing file",
    "PSF-DOC-005": "link targets an anchor that does not exist",
    "PSF-DOC-006": "fenced code block has no language",
    "PSF-DOC-007": "trailing whitespace",
    "PSF-DOC-008": "tab character",
    "PSF-DOC-009": "unclosed fenced code block",
    "PSF-DOC-010": "heading level jumps by more than one",
    "PSF-DOC-011": "page has no level-1 heading",
    "PSF-DOC-012": "page has more than one level-1 heading",
    "PSF-DOC-013": "documentation directory has no pages",
    "PSF-DOC-014": "unrendered template or escaped-HTML artifact",
}


@dataclass(frozen=True, order=True)
class Finding:
    """One documentation defect."""

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


def github_anchor(heading: str) -> str:
    """Slugify a heading the way GitHub does.

    Keeps letters, digits, spaces, hyphens and underscores, lowercases the text
    and turns spaces into hyphens. Emoji and punctuation are dropped.
    """
    text = re.sub(r"`([^`]*)`", r"\1", heading)
    text = re.sub(r"[*_]{1,3}([^*_]+)[*_]{1,3}", r"\1", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    slug = "".join(char for char in text.strip().lower() if char.isalnum() or char in " -_")
    return slug.replace(" ", "-")


def markdown_pages(docs: Path) -> list[Path]:
    """Return every Markdown page under ``docs`` in a stable order."""
    return sorted(path for path in docs.rglob("*.md") if path.is_file())


def prose_lines(text: str) -> list[tuple[int, str]]:
    """Return ``(line number, text)`` for lines outside fenced code blocks."""
    result: list[tuple[int, str]] = []
    in_fence = False
    for number, line in enumerate(text.splitlines(), start=1):
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if not in_fence:
            result.append((number, line))
    return result


def headings(text: str) -> list[tuple[int, int, str]]:
    """Return ``(line, level, text)`` for every heading outside code blocks."""
    found: list[tuple[int, int, str]] = []
    for number, line in prose_lines(text):
        match = HEADING.match(line)
        if match:
            found.append((number, len(match.group("marks")), match.group("text")))
    return found


def _relative(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _link_targets(text: str) -> list[tuple[int, str]]:
    targets: list[tuple[int, str]] = []
    for number, line in prose_lines(text):
        targets.extend((number, match.group("target")) for match in LINK.finditer(line))
    return targets


def _is_local(target: str) -> bool:
    return not target.startswith(("http://", "https://", "mailto:", "tel:", "ftp://", "//"))


def _check_structure(root: Path, docs: Path) -> list[Finding]:
    findings: list[Finding] = []
    index = docs / INDEX_NAME
    if not docs.is_dir():
        return [Finding(str(docs), 1, "PSF-DOC-002", f"documentation directory is missing: {docs}")]
    if not index.is_file():
        findings.append(
            Finding(_relative(index, root), 1, "PSF-DOC-002", "docs/README.md must exist")
        )
    for section in REQUIRED_SECTIONS:
        directory = docs / section
        if not directory.is_dir():
            findings.append(
                Finding(
                    _relative(directory, root),
                    1,
                    "PSF-DOC-001",
                    f"required documentation directory is missing: {section}/",
                )
            )
        elif not any(directory.rglob("*.md")):
            findings.append(
                Finding(
                    _relative(directory, root),
                    1,
                    "PSF-DOC-013",
                    f"{section}/ contains no Markdown pages",
                )
            )
    return findings


def _check_navigation(root: Path, docs: Path, pages: Iterable[Path]) -> list[Finding]:
    index = docs / INDEX_NAME
    if not index.is_file():
        return []
    linked = {
        (index.parent / target.split("#", 1)[0]).resolve()
        for _, target in _link_targets(index.read_text(encoding="utf-8"))
        if _is_local(target) and target.split("#", 1)[0].endswith(".md")
    }
    findings: list[Finding] = []
    for page in pages:
        if page.parent == docs and page.name in NAV_IGNORED:
            continue
        if page.resolve() not in linked:
            findings.append(
                Finding(
                    _relative(page, root),
                    1,
                    "PSF-DOC-003",
                    f"page is not linked from {INDEX_NAME}",
                )
            )
    return findings


def _check_page(
    root: Path, page: Path, docs: Path, anchor_cache: dict[Path, set[str]]
) -> list[Finding]:
    findings: list[Finding] = []
    text = page.read_text(encoding="utf-8")
    relative = _relative(page, root)

    def anchors_for(target: Path) -> set[str]:
        if target not in anchor_cache:
            content = target.read_text(encoding="utf-8") if target.is_file() else ""
            anchor_cache[target] = {github_anchor(item[2]) for item in headings(content)}
        return anchor_cache[target]

    h1 = 0
    previous_level = 0
    in_fence = False
    fence_line = 0

    for number, line in enumerate(text.splitlines(), start=1):
        if FENCE.match(line):
            if not in_fence and not FENCE.match(line).group("info"):  # type: ignore[union-attr]
                findings.append(
                    Finding(relative, number, "PSF-DOC-006", "fenced block declares no language")
                )
            in_fence = not in_fence
            fence_line = number
            continue
        if in_fence:
            continue

        if TEMPLATE_ARTIFACT.search(line):
            findings.append(
                Finding(relative, number, "PSF-DOC-014", "unrendered template artifact")
            )
        if line.rstrip() != line:
            findings.append(Finding(relative, number, "PSF-DOC-007", "trailing whitespace"))
        if "\t" in line:
            findings.append(Finding(relative, number, "PSF-DOC-008", "tab character"))

        heading_match = HEADING.match(line)
        if heading_match:
            level = len(heading_match.group("marks"))
            h1 += level == 1
            if previous_level and level > previous_level + 1:
                findings.append(
                    Finding(
                        relative,
                        number,
                        "PSF-DOC-010",
                        f"heading jumps from h{previous_level} to h{level}",
                    )
                )
            previous_level = level

    if in_fence:
        findings.append(Finding(relative, fence_line, "PSF-DOC-009", "unclosed fenced block"))
    if h1 == 0:
        findings.append(Finding(relative, 1, "PSF-DOC-011", "page has no level-1 heading"))
    elif h1 > 1:
        findings.append(Finding(relative, 1, "PSF-DOC-012", f"{h1} level-1 headings"))

    for number, target in _link_targets(text):
        if not _is_local(target):
            continue
        location, _, fragment = target.partition("#")
        destination = (page.parent / location).resolve() if location else page.resolve()
        if not destination.exists():
            findings.append(
                Finding(
                    relative,
                    number,
                    "PSF-DOC-004",
                    f"missing link target: {target}",
                )
            )
            continue
        if fragment and destination.suffix == ".md" and fragment not in anchors_for(destination):
            findings.append(
                Finding(
                    relative,
                    number,
                    "PSF-DOC-005",
                    f"missing anchor '{fragment}' in {target}",
                )
            )
    return findings


def check_docs(root: Path = REPO_ROOT, docs_dir: Path | None = None) -> list[Finding]:
    """Validate the documentation tree and return every finding.

    Args:
        root: repository root used to render relative paths.
        docs_dir: documentation directory; defaults to ``root/docs``.
    """
    docs = docs_dir if docs_dir is not None else root / "docs"
    findings = _check_structure(root, docs)
    if not docs.is_dir():
        return sorted(findings)

    pages = markdown_pages(docs)
    findings.extend(_check_navigation(root, docs, pages))
    cache: dict[Path, set[str]] = {}
    for page in pages:
        findings.extend(_check_page(root, page, docs, cache))
    return sorted(set(findings))


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point: print findings, exit non-zero when any exist."""
    parser = argparse.ArgumentParser(
        prog="python -m automation.docs",
        description="Validate the docs/ tree: structure, navigation, links and anchors.",
    )
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help="repository root")
    parser.add_argument("--docs", type=Path, default=None, help="documentation directory")
    parser.add_argument("--json", action="store_true", help="emit JSON findings")
    args = parser.parse_args(argv)

    findings = check_docs(args.root, args.docs)
    if args.json:
        print(json.dumps([finding.to_dict() for finding in findings], indent=2))
    else:
        for finding in findings:
            print(finding.format())
        pages = len(markdown_pages(args.docs or args.root / "docs"))
        status = "ok" if not findings else f"{len(findings)} finding(s)"
        print(f"docs: {pages} page(s), {status}")
    return 1 if findings else 0


if __name__ == "__main__":  # pragma: no cover - module entry point
    raise SystemExit(main())
