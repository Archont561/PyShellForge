"""Tests for ``automation.agents``."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from automation.agents import generate


def section(name: str, body: str | None = None) -> str:
    """Return one generated section with its markers."""
    title = generate.TITLES[name]
    content = body if body is not None else f"A real fact about the {name} section."
    return f"{generate.begin_marker(name)}\n## {title}\n{content}\n{generate.end_marker(name)}"


def build(root: Path, body: str | None = None) -> Path:
    """Write a valid AGENTS.md into ``root`` and return it."""
    text = "# AGENTS.md\n\n## Notes\nHand-written notes are preserved.\n\n"
    text += body if body is not None else "\n\n".join(section(name) for name in generate.SECTIONS)
    path = root / "AGENTS.md"
    path.write_text(text + "\n", encoding="utf-8")
    return path


def codes(root: Path) -> set[str]:
    return {finding.code for finding in generate.check_agents(root)}


def test_a_curated_file_passes(tmp_path: Path) -> None:
    build(tmp_path)
    assert generate.check_agents(tmp_path) == []


def test_missing_file_is_reported(tmp_path: Path) -> None:
    assert codes(tmp_path) == {"PSF-AGENT-001"}


def test_missing_marker_is_reported(tmp_path: Path) -> None:
    build(tmp_path, "\n\n".join(section(name) for name in generate.SECTIONS[1:]))
    assert "PSF-AGENT-002" in codes(tmp_path)


def test_out_of_order_sections_are_reported(tmp_path: Path) -> None:
    reordered = list(generate.SECTIONS)
    reordered[0], reordered[1] = reordered[1], reordered[0]
    build(tmp_path, "\n\n".join(section(name) for name in reordered))
    assert "PSF-AGENT-003" in codes(tmp_path)


def test_empty_section_is_reported(tmp_path: Path) -> None:
    body = "\n\n".join(section(name) for name in generate.SECTIONS)
    body = body.replace(
        section("commands"),
        f"{generate.begin_marker('commands')}\n{generate.end_marker('commands')}",
    )
    build(tmp_path, body)
    assert "PSF-AGENT-004" in codes(tmp_path)


def test_stub_is_reported(tmp_path: Path) -> None:
    body = "\n\n".join(
        section(name, f"{generate.STUB} describe the {name} section_") for name in generate.SECTIONS
    )
    build(tmp_path, body)
    findings = generate.check_agents(tmp_path)
    stub_findings = [finding for finding in findings if finding.code == "PSF-AGENT-005"]
    assert len(stub_findings) == len(generate.SECTIONS)
    assert all(finding.path == "AGENTS.md" and finding.line > 1 for finding in stub_findings)


def test_wrong_heading_is_reported(tmp_path: Path) -> None:
    body = "\n\n".join(section(name) for name in generate.SECTIONS)
    body = body.replace("## Commands", "## How to run things")
    build(tmp_path, body)
    assert "PSF-AGENT-007" in codes(tmp_path)


def test_sidecar_is_reported(tmp_path: Path) -> None:
    build(tmp_path)
    (tmp_path / "AGENTS.generated.md").write_text("# AGENTS.md\n", encoding="utf-8")
    assert codes(tmp_path) == {"PSF-AGENT-006"}


def test_section_body_reports_absent_and_empty_markers(tmp_path: Path) -> None:
    assert generate.section_body("no markers here", "overview") is None
    assert generate.section_body(generate.begin_marker("overview"), "overview") is None
    empty = f"{generate.begin_marker('overview')}\n{generate.end_marker('overview')}"
    assert generate.section_body(empty, "overview") == ""


def test_markers_in_returns_file_order() -> None:
    text = f"{generate.begin_marker('testing')}\n{generate.begin_marker('overview')}"
    assert generate.markers_in(text) == ["testing", "overview"]


def test_pinned_version_requires_an_exact_pin(tmp_path: Path) -> None:
    path = tmp_path / "package.json"
    path.write_text(
        json.dumps({"devDependencies": {generate.CLI_PACKAGE: "0.1.0"}}), encoding="utf-8"
    )
    assert generate.pinned_version(path) == "0.1.0"

    path.write_text(
        json.dumps({"devDependencies": {generate.CLI_PACKAGE: "^0.1.0"}}), encoding="utf-8"
    )
    with pytest.raises(ValueError):
        generate.pinned_version(path)

    path.write_text(json.dumps({"devDependencies": {}}), encoding="utf-8")
    with pytest.raises(ValueError, match="not pinned"):
        generate.pinned_version(path)


def test_generator_command_uses_npx_with_the_pin_and_no_symlink() -> None:
    command = generate.generator_command("0.1.0")
    assert command[0].startswith("npx")
    assert f"{generate.CLI_PACKAGE}@0.1.0" in command
    assert "--no-symlink" in command


def test_bootstrap_refuses_to_overwrite_a_marked_file(tmp_path: Path) -> None:
    build(tmp_path)
    calls: list[tuple[tuple[str, ...], Path]] = []

    def runner(command: tuple[str, ...], *, cwd: Path) -> int:
        calls.append((command, cwd))
        return 0

    assert generate.bootstrap(root=tmp_path, runner=runner) is False
    assert calls == []


def test_bootstrap_runs_the_cli_when_the_file_has_no_markers(tmp_path: Path) -> None:
    (tmp_path / "AGENTS.md").write_text("# Agent instructions\n", encoding="utf-8")
    (tmp_path / "package.json").write_text(
        json.dumps({"devDependencies": {generate.CLI_PACKAGE: "0.1.0"}}), encoding="utf-8"
    )
    calls: list[tuple[str, ...]] = []

    def runner(command: tuple[str, ...], *, cwd: Path) -> int:
        calls.append(command)
        build(tmp_path)
        return 0

    assert generate.bootstrap(root=tmp_path, runner=runner) is True
    assert calls and f"{generate.CLI_PACKAGE}@0.1.0" in calls[0]


def test_bootstrap_force_rewrites_even_with_markers(tmp_path: Path) -> None:
    build(tmp_path)
    (tmp_path / "package.json").write_text(
        json.dumps({"devDependencies": {generate.CLI_PACKAGE: "0.1.0"}}), encoding="utf-8"
    )

    def runner(command: tuple[str, ...], *, cwd: Path) -> int:
        return 0

    assert generate.bootstrap(root=tmp_path, runner=runner, force=True) is True


def test_main_reports_findings_as_json(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert generate.main(["--root", str(tmp_path), "--json"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload[0]["code"] == "PSF-AGENT-001"


def test_main_checks_a_valid_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    build(tmp_path)
    assert generate.main(["--root", str(tmp_path), "--check"]) == 0
    assert "9 section(s), ok" in capsys.readouterr().out


def test_main_refuses_bootstrap_on_a_marked_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    build(tmp_path)
    assert generate.main(["--root", str(tmp_path), "--bootstrap"]) == 1
    assert "refusing to overwrite" in capsys.readouterr().out


def test_main_bootstrap_reports_the_stub_count(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(generate, "bootstrap", lambda **kwargs: True)
    monkeypatch.setattr(generate, "check_agents", lambda root: [])
    assert generate.main(["--root", str(tmp_path), "--bootstrap"]) == 0
    assert "0 stub(s) to fill in" in capsys.readouterr().out
