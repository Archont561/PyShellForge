"""Steps for ``automation/features/agents_file.feature``."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pytest_bdd import given, then, when

from automation.agents import generate


def _section(name: str) -> str:
    body = f"Documented fact about {name}."
    return f"{generate.begin_marker(name)}\n## {generate.TITLES[name]}\n{body}\n{generate.end_marker(name)}"


def scaffold(root: Path) -> Path:
    """Write a curated ``AGENTS.md`` and return the repository root."""
    root.mkdir(parents=True, exist_ok=True)
    text = "# AGENTS.md\n\n" + "\n\n".join(_section(name) for name in generate.SECTIONS)
    (root / "AGENTS.md").write_text(text + "\n\n## Notes\nHuman-owned.\n", encoding="utf-8")
    return root


@given("an AGENTS.md that carries every generated section")
def curated(tmp_path: Path, context: dict[str, Any]) -> None:
    context["root"] = scaffold(tmp_path / "repo")


@given("an AGENTS.md where the commands section lost its markers")
def lost_markers(tmp_path: Path, context: dict[str, Any]) -> None:
    root = scaffold(tmp_path / "repo")
    page = root / "AGENTS.md"
    page.write_text(
        page.read_text(encoding="utf-8").replace(generate.begin_marker("commands"), ""),
        encoding="utf-8",
    )
    context["root"] = root


@given("an AGENTS.md with an unfinished agents-md stub")
def unfinished_stub(tmp_path: Path, context: dict[str, Any]) -> None:
    root = scaffold(tmp_path / "repo")
    page = root / "AGENTS.md"
    page.write_text(
        page.read_text(encoding="utf-8").replace(
            "Documented fact about testing.", f"{generate.STUB} describe the testing setup_"
        ),
        encoding="utf-8",
    )
    context["root"] = root


@given("an AGENTS.generated.md sidecar next to AGENTS.md")
def sidecar(tmp_path: Path, context: dict[str, Any]) -> None:
    root = scaffold(tmp_path / "repo")
    (root / "AGENTS.generated.md").write_text("# AGENTS.md\n", encoding="utf-8")
    context["root"] = root


@when("I check the agent instructions")
def check(context: dict[str, Any]) -> None:
    context["findings"] = generate.check_agents(Path(str(context["root"])))


@when("I bootstrap the agent instructions")
def bootstrap(context: dict[str, Any]) -> None:
    root = Path(str(context["root"]))
    calls: list[list[str]] = []

    def runner(command: list[str], *, cwd: Path) -> int:
        calls.append(list(command))
        return 0

    context["ran"] = generate.bootstrap(root=root, runner=runner)
    context["calls"] = calls


@then("the agent instructions are valid")
def valid(context: dict[str, Any]) -> None:
    findings = context["findings"]
    assert findings == [], [finding.format() for finding in findings]


@then("the agent instructions report PSF-AGENT-002")
def reports_markers(context: dict[str, Any]) -> None:
    codes = {finding.code for finding in context["findings"]}
    assert "PSF-AGENT-002" in codes, sorted(codes)


@then("the agent instructions report PSF-AGENT-005")
def reports_stub(context: dict[str, Any]) -> None:
    codes = {finding.code for finding in context["findings"]}
    assert "PSF-AGENT-005" in codes, sorted(codes)


@then("the agent instructions report PSF-AGENT-006")
def reports_sidecar(context: dict[str, Any]) -> None:
    codes = {finding.code for finding in context["findings"]}
    assert "PSF-AGENT-006" in codes, sorted(codes)


@then("the bootstrap is refused without running the generator")
def refused(context: dict[str, Any]) -> None:
    assert context["ran"] is False
    assert context["calls"] == []
