"""The generated READMEs are produced by readme-md-generator — keep them honest.

Two files come out of ``python -m automation.readme``, both rendered from
``automation/readme/README.ejs``, whose metadata comes from ``package.json``: the
repository ``README.md`` and ``pyshellforge/README.md``, the long description the
package metadata points at (hatchling refuses a readme outside the project
directory, and PyPI needs one inside it).

These tests check the parts that can be verified offline: structure, anchors,
template hygiene, that the two copies agree once the rebased links are undone,
that the metadata cannot drift away from ``pyproject.toml``, and that every
in-repo link points at a file that exists relative to its own copy.

Set ``PSF_CHECK_README=1`` to additionally regenerate the README with the real
generator and fail if the committed file is stale.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path
from urllib.parse import quote

import pytest

pytestmark = pytest.mark.integration

#: The project directory (``pyshellforge/``), which holds the manifest and its copy.
PROJECT = Path(__file__).resolve().parents[2]
#: The repository root, which holds the tooling and the repository README.
ROOT = PROJECT.parent
README = ROOT / "README.md"
PROJECT_READMES = (PROJECT / "README.md", ROOT / "README.md")
TEMPLATE = ROOT / "automation" / "readme" / "README.ejs"
GENERATOR = ROOT / "automation" / "readme" / "generate.py"
PYPROJECT_PATH = PROJECT / "pyproject.toml"
PACKAGE_JSON_PATH = ROOT / "package.json"

GENERATOR_URL = "https://github.com/kefranabg/readme-md-generator"

#: The Author website line. It belongs to the template, not to the generator.
WEBSITE_LINE = (
    "- Website: [archont561.github.io/Archont561](https://archont561.github.io/Archont561/)"
)

#: Sections the README must keep, whatever the template looks like. The page is
#: deliberately small: everything that is not a landing-page concern belongs in
#: ``docs/``, which the Documentation section links.
REQUIRED_SECTIONS = [
    "Documentation",
    "Install",
    "Usage",
    "Run tests",
    "Author",
    "Contributing",
    "Show your support",
    "License",
]

#: Documentation the landing page routes into, relative to the repository root.
DOCS_PAGES = sorted(page.relative_to(ROOT).as_posix() for page in (ROOT / "docs").rglob("*.md"))


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def readme_text() -> str:
    return README.read_text(encoding="utf-8")


def package_json() -> dict[str, object]:
    return json.loads(PACKAGE_JSON_PATH.read_text(encoding="utf-8"))


def pyproject() -> dict[str, object]:
    return tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))


def headings(text: str) -> list[str]:
    return [match.group(2) for match in re.finditer(r"^(#{1,6})\s+(.*?)\s*$", text, re.M)]


def fenced_blocks(text: str) -> list[tuple[str, str]]:
    pattern = re.compile(r"^```(?P<language>[\w+-]*)\n(?P<body>.*?)^```$", re.M | re.S)
    return [
        (match.group("language"), match.group("body").rstrip("\n"))
        for match in pattern.finditer(text)
    ]


# ---------------------------------------------------------------------------
# the file is generated, not written
# ---------------------------------------------------------------------------
def test_readme_exists() -> None:
    assert README.is_file()


def test_readme_credits_readme_md_generator() -> None:
    text = readme_text()
    assert GENERATOR_URL in text
    assert "This README was generated" in text
    assert "automation/readme/README.ejs" in text


def test_template_and_driver_exist() -> None:
    assert TEMPLATE.is_file(), "the ejs template is the source of truth for README.md"
    assert GENERATOR.is_file(), "npm run readme drives readme-md-generator"


def test_npm_scripts_are_wrapped_by_python() -> None:
    """The npm scripts must delegate to the Python driver, not to Node code."""
    scripts = package_json()["scripts"]
    assert isinstance(scripts, dict)
    assert scripts["readme"] == "python -m automation.readme"
    assert scripts["readme:check"] == "python -m automation.readme --check"


def test_generator_version_is_pinned() -> None:
    dev_dependencies = package_json()["devDependencies"]
    assert isinstance(dev_dependencies, dict)
    pinned = dev_dependencies["readme-md-generator"]
    assert re.fullmatch(r"\d+\.\d+\.\d+", str(pinned)), f"pin the generator exactly, got {pinned!r}"


def test_generate_driver_is_python() -> None:
    source = GENERATOR.read_text(encoding="utf-8")
    assert "--check" in source
    assert "readme-md-generator" in source
    # The generator prompts before overwriting, so it must run in a scratch dir.
    assert "mkdtemp" in source
    assert not list((ROOT / "automation").rglob("*.js")), "repository tooling is Python only"


# ---------------------------------------------------------------------------
# template hygiene
# ---------------------------------------------------------------------------
def test_no_template_artifacts_leaked() -> None:
    text = readme_text()
    for marker in ("<%", "%>", "&#34;", "&#39;", "[object Object]", "undefined"):
        assert marker not in text, f"unrendered template artifact {marker!r} in README.md"


def test_author_website_is_template_owned() -> None:
    """The Author website must not come from the generator's GitHub API lookup.

    readme-md-generator fills ``authorWebsite`` from
    ``https://api.github.com/users/<name>`` without a token, and returns nothing
    when that lookup is rate limited. It then drops the line, and readme-check
    fails on a README that did not change, so the template carries the URL.
    """
    template = TEMPLATE.read_text(encoding="utf-8")
    assert "- Website: [<%- authorWebsite" not in template, (
        "the Author website must be a literal, not the generator's API lookup"
    )
    assert WEBSITE_LINE in template
    for readme in PROJECT_READMES:
        content = readme.read_text(encoding="utf-8")
        assert WEBSITE_LINE in content, f"{readme} lost the website line"


def test_code_fences_are_balanced() -> None:
    text = readme_text()
    fences = re.findall(r"^```", text, re.M)
    assert len(fences) % 2 == 0, "unbalanced ``` fences"
    assert len(fenced_blocks(text)) == len(fences) // 2


def test_no_trailing_whitespace_and_single_final_newline() -> None:
    text = readme_text()
    assert text.endswith("\n") and not text.endswith("\n\n")
    offenders = [
        f"line {index}"
        for index, line in enumerate(text.splitlines(), start=1)
        if line != line.rstrip()
    ]
    assert offenders == [], f"trailing whitespace on {offenders[:5]}"


# ---------------------------------------------------------------------------
# structure
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("section", REQUIRED_SECTIONS)
def test_required_section_present(section: str) -> None:
    assert any(section in heading for heading in headings(readme_text())), (
        f"missing '{section}' section"
    )


def test_documentation_section_routes_every_page() -> None:
    """The landing page names its documentation instead of repeating it."""
    linked = set(re.findall(r"\]\(([^)\s#]+)", readme_text()))
    assert "docs/README.md" in linked, "the README should link the documentation index"
    missing = sorted(set(DOCS_PAGES) - linked)
    assert missing == [], f"documentation the README never mentions: {missing}"


# ---------------------------------------------------------------------------
# metadata cannot drift
# ---------------------------------------------------------------------------
def test_title_matches_the_package_name() -> None:
    """The human-facing title must still be the distribution name."""
    heading = re.search(r'<h1 align="center">([^<]+)</h1>', readme_text())
    assert heading is not None
    assert heading.group(1).lower() == package_json()["name"]


def test_version_badge_matches_package_version() -> None:
    import pyshellforge

    text = readme_text()
    assert f"version-{pyshellforge.VERSION}-blue" in text
    assert f"version-{package_json()['version']}" in text


def test_the_package_version_is_the_badge_version() -> None:
    """The README, ``pyproject.toml`` and the imported attribute agree."""
    import pyshellforge

    assert pyproject()["project"]["version"] == pyshellforge.VERSION  # type: ignore[index]


def test_package_json_version_matches_pyproject() -> None:
    assert package_json()["version"] == pyproject()["project"]["version"]  # type: ignore[index]


def test_package_json_mirrors_pyproject_metadata() -> None:
    project = pyproject()["project"]
    package = package_json()
    assert isinstance(project, dict)
    assert package["name"] == project["name"]
    assert package["description"] == project["description"]
    assert package["license"] == project["license"]["text"]
    assert package["homepage"] == f"{project['urls']['Repository']}#readme"  # type: ignore[index]


def test_prerequisites_come_from_engines() -> None:
    engines = package_json()["engines"]
    assert isinstance(engines, dict)
    project = pyproject()["project"]
    assert isinstance(project, dict)
    assert engines["python"] == project["requires-python"]
    text = readme_text()
    python = str(engines["python"])
    # The badge keeps the exact bound in its URL-encoded source, and spells it out
    # in the alt text: a bare `>` ends the HTML tag, so the badge broke and the
    # rest of the element leaked into the page instead of rendering.
    assert f"python-{quote(python, safe='')}-blue" in text
    assert f'alt="python {python.removeprefix(">=")}+"' in text
    assert 'alt="python >' not in text
    # Nothing renders shell yet, so the README must not claim a shell prerequisite.
    assert "bash" not in engines


def test_author_and_license_sections_are_filled_from_metadata() -> None:
    text = readme_text()
    author = package_json()["author"]
    assert isinstance(author, dict)
    assert str(author["name"]) in text
    assert "[MIT](" in text


# ---------------------------------------------------------------------------
# links
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("readme", PROJECT_READMES, ids=lambda path: path.name)
def test_relative_links_resolve(readme: Path) -> None:
    """Every in-repo link points at a file that exists beside that copy."""
    text = readme.read_text(encoding="utf-8")
    targets = re.findall(r"\]\(([^)\s#]+)(?:#[^)]*)?\)", text)
    relative = [
        target
        for target in targets
        if not target.startswith(("http://", "https://", "mailto:", "#"))
    ]
    assert relative, "the README should link to the docs and the changelog"
    missing = [target for target in relative if not (readme.parent / target).exists()]
    assert missing == [], f"broken relative links in {readme}: {missing}"


def test_the_project_copy_only_rebases_relative_links() -> None:
    """The two copies are the same page: the nested one only rebases its links."""
    nested = (PROJECT / "README.md").read_text(encoding="utf-8")
    rebased_back = re.sub(r"\]\(\.\./", "](", nested)
    assert rebased_back == readme_text()


def test_the_nested_readme_is_the_packaging_readme() -> None:
    """``[project].readme`` must point at the copy inside the project directory."""
    project = pyproject()["project"]
    assert project["readme"] == "README.md"  # type: ignore[index]
    assert (PROJECT / str(project["readme"])).is_file()  # type: ignore[index]


# ---------------------------------------------------------------------------
# the README makes no claim the package cannot back
# ---------------------------------------------------------------------------
def test_readme_does_not_promise_a_renderer() -> None:
    """The skeleton ships ``VERSION``; the landing page must not document more."""
    text = " ".join(readme_text().split())
    assert "exposes `VERSION` and nothing else" in text
    for absent in ("psf render", "psf validate", "ShellScript("):
        assert absent not in text, f"the README documents {absent!r}, which does not exist"


def test_the_status_page_states_what_is_missing() -> None:
    """Moving prose into ``docs/`` must not soften it."""
    page = ROOT / "docs" / "concepts" / "version-only-scaffold.md"
    text = " ".join(page.read_text(encoding="utf-8").split())
    assert "There is no renderer, no AST and no CLI yet" in text
    for absent in ("psf render", "psf validate", "ShellScript("):
        assert absent not in text, f"the status page documents {absent!r}"


# ---------------------------------------------------------------------------
# full regeneration check (needs node + network for npx)
# ---------------------------------------------------------------------------
@pytest.mark.skipif(
    os.environ.get("PSF_CHECK_README") != "1",
    reason="set PSF_CHECK_README=1 to regenerate README.md with readme-md-generator",
)
def test_readme_is_not_stale() -> None:
    if shutil.which("node") is None:  # pragma: no cover - depends on the environment
        pytest.skip("node is not installed")
    result = subprocess.run(
        [sys.executable, "-m", "automation.readme", "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
