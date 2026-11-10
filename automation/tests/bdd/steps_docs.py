"""Steps for ``automation/features/docs_validation.feature``."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from pytest_bdd import given, parsers, then, when

from automation.docs import check

#: The tree the validator requires; ``docs/development/`` is the only section
#: that has pages while the package is a skeleton.
SECTIONS: tuple[tuple[str, str, str], ...] = (("development", "testing", "Testing"),)

SECTION, PAGE_NAME, _TITLE = SECTIONS[0]
PAGE = f"{SECTION}/{PAGE_NAME}.md"


def _index() -> str:
    lines = ["# Documentation", "", "Start here, then follow the links.", ""]
    for section, name, title in SECTIONS:
        lines.append(f"- [{title}]({section}/{name}.md)")
    return "\n".join(lines) + "\n"


def _page(title: str) -> str:
    return f"# {title}\n\nBack to the [index](../README.md).\n"


def scaffold(docs: Path) -> Path:
    """Create a documentation tree that passes every check."""
    docs.mkdir(parents=True, exist_ok=True)
    (docs / "README.md").write_text(_index(), encoding="utf-8")
    for section, name, title in SECTIONS:
        directory = docs / section
        directory.mkdir(exist_ok=True)
        (directory / f"{name}.md").write_text(_page(title), encoding="utf-8")
    return docs.parent


@given("a documentation tree with every required section")
def documentation_tree(tmp_path: Path, context: dict[str, Any]) -> None:
    context["root"] = scaffold(tmp_path / "repo" / "docs")


@given("the documentation tree is complete")
def complete_tree() -> None:
    """The Background already scaffolded every required section."""


@given("a page that the index does not link to")
def orphan_page(context: dict[str, Any]) -> None:
    docs = Path(str(context["root"])) / "docs"
    (docs / SECTION / "orphan.md").write_text(_page("Orphan"), encoding="utf-8")


@given("a page that links to a file that does not exist")
def broken_link(context: dict[str, Any]) -> None:
    page = Path(str(context["root"])) / "docs" / PAGE
    page.write_text(
        page.read_text(encoding="utf-8") + "\nSee [the missing page](./missing.md).\n",
        encoding="utf-8",
    )


@given("a page that links to an anchor that does not exist")
def broken_anchor(context: dict[str, Any]) -> None:
    page = Path(str(context["root"])) / "docs" / PAGE
    page.write_text(
        page.read_text(encoding="utf-8") + f"\nSee [nowhere]({PAGE_NAME}.md#missing-anchor).\n",
        encoding="utf-8",
    )


@given("the development section is removed")
def remove_section(context: dict[str, Any]) -> None:
    docs = Path(str(context["root"])) / "docs"
    shutil.rmtree(docs / SECTION)
    index = docs / "README.md"
    lines = [line for line in index.read_text(encoding="utf-8").splitlines() if PAGE not in line]
    index.write_text("\n".join(lines) + "\n", encoding="utf-8")


@given("a page with a fenced code block without a language")
def fenceless_block(context: dict[str, Any]) -> None:
    page = Path(str(context["root"])) / "docs" / PAGE
    page.write_text(
        page.read_text(encoding="utf-8") + "\n```\npixi run test-all\n```\n",
        encoding="utf-8",
    )


@given("a page with an unclosed fenced code block")
def unclosed_block(context: dict[str, Any]) -> None:
    page = Path(str(context["root"])) / "docs" / PAGE
    page.write_text(
        page.read_text(encoding="utf-8") + "\n```bash\npytest -q\n",
        encoding="utf-8",
    )


@when("I validate the documentation")
def validate(context: dict[str, Any]) -> None:
    context["findings"] = check.check_docs(root=Path(str(context["root"])))


@then("the documentation is valid")
def no_findings(context: dict[str, Any]) -> None:
    findings = context["findings"]
    assert findings == [], [finding.format() for finding in findings]


@then(parsers.parse("validation reports {code}"))
def reports(context: dict[str, Any], code: str) -> None:
    findings = context["findings"]
    codes = {finding.code for finding in findings}
    assert code in codes, sorted(codes)
