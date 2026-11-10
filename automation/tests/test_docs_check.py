"""Tests for ``automation.docs``."""

from __future__ import annotations

from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

from automation.docs import check

SECTIONS = check.REQUIRED_SECTIONS


def build(root: Path) -> Path:
    """Create a valid documentation tree and return the repository root."""
    docs = root / "docs"
    docs.mkdir(parents=True)
    index = ["# Documentation", ""]
    for section in SECTIONS:
        directory = docs / section
        directory.mkdir()
        page = directory / "page.md"
        page.write_text("# Page\n\nBack to the [index](../README.md).\n", encoding="utf-8")
        index.append(f"- [{section}]({section}/page.md)")
    (docs / "README.md").write_text("\n".join(index) + "\n", encoding="utf-8")
    return root


def codes(root: Path) -> set[str]:
    return {finding.code for finding in check.check_docs(root)}


def test_valid_tree_has_no_findings(tmp_path: Path) -> None:
    assert check.check_docs(build(tmp_path)) == []


def test_missing_docs_directory(tmp_path: Path) -> None:
    assert "PSF-DOC-002" in codes(tmp_path)


def test_missing_index(tmp_path: Path) -> None:
    root = build(tmp_path)
    (root / "docs" / "README.md").unlink()
    assert "PSF-DOC-002" in codes(root)


def test_missing_section(tmp_path: Path) -> None:
    root = build(tmp_path)
    (root / "docs" / SECTIONS[0] / "page.md").unlink()
    (root / "docs" / SECTIONS[0]).rmdir()
    assert "PSF-DOC-001" in codes(root)


def test_empty_section(tmp_path: Path) -> None:
    root = build(tmp_path)
    (root / "docs" / SECTIONS[0] / "page.md").unlink()
    assert "PSF-DOC-013" in codes(root)


def test_orphan_page(tmp_path: Path) -> None:
    root = build(tmp_path)
    (root / "docs" / SECTIONS[0] / "extra.md").write_text("# Extra\n", encoding="utf-8")
    assert "PSF-DOC-003" in codes(root)


def test_broken_relative_link(tmp_path: Path) -> None:
    root = build(tmp_path)
    page = root / "docs" / SECTIONS[0] / "page.md"
    page.write_text(page.read_text() + "\n[x](./missing.md)\n", encoding="utf-8")
    assert "PSF-DOC-004" in codes(root)


def test_broken_anchor(tmp_path: Path) -> None:
    root = build(tmp_path)
    page = root / "docs" / SECTIONS[0] / "page.md"
    page.write_text(page.read_text() + "\n[x](page.md#nope)\n", encoding="utf-8")
    assert "PSF-DOC-005" in codes(root)


def test_valid_anchor(tmp_path: Path) -> None:
    root = build(tmp_path)
    (root / "docs" / SECTIONS[0] / "page.md").write_text("# Safety model\n", encoding="utf-8")
    page = root / "docs" / SECTIONS[0] / "page.md"
    page.write_text(
        page.read_text() + f"\n[x](../{SECTIONS[0]}/page.md#safety-model)\n", encoding="utf-8"
    )
    assert check.check_docs(root) == []


def test_fence_without_language(tmp_path: Path) -> None:
    root = build(tmp_path)
    page = root / "docs" / SECTIONS[0] / "page.md"
    page.write_text(page.read_text() + "\n```\ncode\n```\n", encoding="utf-8")
    assert "PSF-DOC-006" in codes(root)


def test_unclosed_fence(tmp_path: Path) -> None:
    root = build(tmp_path)
    page = root / "docs" / SECTIONS[0] / "page.md"
    page.write_text(page.read_text() + "\n```bash\npytest\n", encoding="utf-8")
    assert "PSF-DOC-009" in codes(root)


def test_trailing_whitespace_and_tabs(tmp_path: Path) -> None:
    root = build(tmp_path)
    page = root / "docs" / SECTIONS[0] / "page.md"
    page.write_text("# Page \n\n\ttabbed\n", encoding="utf-8")
    found = codes(root)
    assert "PSF-DOC-007" in found
    assert "PSF-DOC-008" in found


def test_heading_level_jump(tmp_path: Path) -> None:
    root = build(tmp_path)
    page = root / "docs" / SECTIONS[0] / "page.md"
    page.write_text("# Page\n\n### Deep\n", encoding="utf-8")
    assert "PSF-DOC-010" in codes(root)


def test_missing_h1(tmp_path: Path) -> None:
    root = build(tmp_path)
    page = root / "docs" / SECTIONS[0] / "page.md"
    page.write_text("## Only an h2\n", encoding="utf-8")
    assert "PSF-DOC-011" in codes(root)


def test_multiple_h1(tmp_path: Path) -> None:
    root = build(tmp_path)
    page = root / "docs" / SECTIONS[0] / "page.md"
    page.write_text("# One\n\n# Two\n", encoding="utf-8")
    assert "PSF-DOC-012" in codes(root)


def test_template_artifact(tmp_path: Path) -> None:
    root = build(tmp_path)
    page = root / "docs" / SECTIONS[0] / "page.md"
    page.write_text("# Page\n\n<%- projectName %>\n", encoding="utf-8")
    assert "PSF-DOC-014" in codes(root)


def test_external_links_are_not_checked(tmp_path: Path) -> None:
    root = build(tmp_path)
    page = root / "docs" / SECTIONS[0] / "page.md"
    page.write_text(page.read_text() + "\n[x](https://example.com/missing)\n", encoding="utf-8")
    assert check.check_docs(root) == []


def test_links_inside_code_blocks_are_ignored(tmp_path: Path) -> None:
    root = build(tmp_path)
    page = root / "docs" / SECTIONS[0] / "page.md"
    page.write_text(
        page.read_text() + '\n```python\nlink = "[x](./missing.md)"\n```\n', encoding="utf-8"
    )
    assert check.check_docs(root) == []


def test_findings_are_sorted_and_formatted(tmp_path: Path) -> None:
    root = build(tmp_path)
    (root / "docs" / SECTIONS[0] / "extra.md").write_text("no heading\n", encoding="utf-8")
    findings = check.check_docs(root)
    assert findings == sorted(findings)
    assert findings[0].format().startswith(f"docs/{SECTIONS[0]}/extra.md:1: PSF-DOC-")


def test_json_payload_is_serialisable(tmp_path: Path) -> None:
    root = build(tmp_path)
    (root / "docs" / SECTIONS[0] / "extra.md").write_text("# Extra\n", encoding="utf-8")
    payload = [finding.to_dict() for finding in check.check_docs(root)]
    assert {"path", "line", "code", "message"} == set(payload[0])


def test_codes_are_documented() -> None:
    codes = set(check.CODES)
    assert len(codes) == len(check.CODES), "duplicate code in CODES"
    assert all(code.startswith("PSF-DOC-") for code in codes)
    assert all(check.CODES[code] for code in codes), "every code needs a description"


@pytest.mark.parametrize(
    ("heading", "expected"),
    [
        ("What it is", "what-it-is"),
        ("🤝 Contributing", "-contributing"),
        ("`psf render`", "psf-render"),
        ("Safety & quoting", "safety--quoting"),
        ("API (v1)", "api-v1"),
    ],
)
def test_github_anchor_examples(heading: str, expected: str) -> None:
    assert check.github_anchor(heading) == expected


@given(st.text(max_size=60))
def test_github_anchor_never_raises(heading: str) -> None:
    anchor = check.github_anchor(heading)
    assert all(char not in anchor for char in " \t\n!@#$%^&*()+=[{]}|;:'\",.<>/?\\")


def test_main_reports_findings_and_exit_code(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = build(tmp_path)
    assert check.main(["--root", str(root)]) == 0
    (root / "docs" / SECTIONS[0] / "extra.md").write_text("# Extra\n", encoding="utf-8")
    assert check.main(["--root", str(root)]) == 1
    assert "PSF-DOC-003" in capsys.readouterr().out


def test_main_json_output(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = build(tmp_path)
    assert check.main(["--root", str(root), "--json"]) == 0
    assert capsys.readouterr().out.strip() == "[]"


def test_headings_ignores_fenced_content(tmp_path: Path) -> None:
    text = "# Title\n\n```bash\n# not a heading\n```\n\n## Real\n"
    assert [heading[2] for heading in check.headings(text)] == ["Title", "Real"]
