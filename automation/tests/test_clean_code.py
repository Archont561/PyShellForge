"""Tests for ``automation.clean_code``."""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path

import pytest

from automation.clean_code import check as clean

CONFIG = Path("/checkout/packages/pyshellforge/pyproject.toml")
TOO_MANY_PARAMETERS = {
    "file": "automation/demo.py",
    "line": 12,
    "column": 0,
    "code": "CC102",
    "message": "Function 'build' has too many parameters (8 > 5)",
    "severity": "warning",
}


class Recorder:
    """A runner that answers with fixed JSON lines and remembers the command."""

    def __init__(self, *records: dict[str, object], noise: str = "") -> None:
        self.records = records
        self.noise = noise
        self.command: tuple[str, ...] = ()

    def __call__(self, command: Sequence[str]) -> str:
        self.command = tuple(command)
        lines = [json.dumps(record) for record in self.records]
        if self.noise:
            lines.insert(0, self.noise)
        return "\n".join(lines)


def finding(**overrides: object) -> dict[str, object]:
    """Return one ``rude`` record, with ``overrides`` applied."""
    return {**TOO_MANY_PARAMETERS, **overrides}


def test_rude_command_passes_the_config_and_the_paths() -> None:
    command = clean.rude_command(["automation", "dodo.py"], CONFIG)
    assert command[1:3] == ["-m", "rude"]
    assert command[3:5] == ["check", "--format"]
    assert "--config" in command
    assert command[command.index("--config") + 1] == str(CONFIG)
    assert command[-2:] == ["automation", "dodo.py"]


def test_parse_findings_reads_json_lines() -> None:
    output = json.dumps(TOO_MANY_PARAMETERS) + "\n"
    assert clean.parse_findings(output) == [
        clean.Finding(
            path="automation/demo.py",
            line=12,
            column=0,
            code="CC102",
            message="Function 'build' has too many parameters (8 > 5)",
        )
    ]


def test_parse_findings_sorts_and_deduplicates() -> None:
    output = "\n".join(
        json.dumps(record)
        for record in (
            finding(line=30),
            finding(line=4),
            finding(line=30, column=8),
            finding(line=4),
        )
    )
    findings = clean.parse_findings(output)
    assert [(item.line, item.column) for item in findings] == [(4, 0), (30, 0), (30, 8)]


def test_a_finding_renders_as_a_located_line() -> None:
    item = clean.Finding(
        path="automation/demo.py", line=12, column=0, code="CC102", message="too many"
    )
    assert item.format() == "automation/demo.py:12:0: CC102 too many"
    assert item.to_dict()["code"] == "CC102"


def test_check_repository_runs_the_gate_command() -> None:
    recorder = Recorder(finding())
    findings = clean.check_repository(("automation",), config=CONFIG, runner=recorder)
    assert [item.code for item in findings] == ["CC102"]
    assert recorder.command == tuple(clean.rude_command(("automation",), CONFIG))


def test_the_gate_covers_both_distributions_and_the_automation() -> None:
    assert clean.SOURCES == (
        "packages/pyshellforge/src",
        "packages/pyshellforge-rude/src",
        "automation",
        "dodo.py",
    )
    assert clean.CONFIG.name == "pyproject.toml"
    assert clean.CONFIG.parent.name == "pyshellforge"


def test_main_reports_a_clean_tree(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(clean, "check_repository", lambda *args, **kwargs: [])
    assert clean.main([]) == 0
    captured = capsys.readouterr()
    assert "ok" in captured.out
    assert captured.err == ""


def test_main_fails_on_findings(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    findings = clean.parse_findings(json.dumps(TOO_MANY_PARAMETERS))
    monkeypatch.setattr(clean, "check_repository", lambda *args, **kwargs: findings)
    assert clean.main(["automation"]) == 1
    captured = capsys.readouterr()
    assert "automation/demo.py:12:0: CC102" in captured.out
    assert "1 finding(s)" in captured.out
    assert "codes: CC102" in captured.err


def test_main_emits_json_when_asked(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    findings = clean.parse_findings(json.dumps(TOO_MANY_PARAMETERS))
    monkeypatch.setattr(clean, "check_repository", lambda *args, **kwargs: findings)
    assert clean.main(["--json"]) == 1
    captured = capsys.readouterr()
    assert json.loads(captured.out)[0]["code"] == "CC102"
    assert captured.err == ""


def test_main_reports_a_tool_failure(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail(*args: object, **kwargs: object) -> list[clean.Finding]:
        msg = "rude is not installed"
        raise RuntimeError(msg)

    monkeypatch.setattr(clean, "check_repository", fail)
    assert clean.main([]) == 2
    assert "clean-code: rude is not installed" in capsys.readouterr().err


def test_subprocess_runner_surfaces_a_tool_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    class Completed:
        returncode = 2
        stdout = ""
        stderr = "boom"

    monkeypatch.setattr(clean.subprocess, "run", lambda *args, **kwargs: Completed())
    with pytest.raises(RuntimeError, match="exited with status 2: boom"):
        clean.subprocess_runner(["rude"])


def test_the_repository_is_clean() -> None:
    """The gate this change adds has to pass on the tree it ships with."""
    assert clean.check_repository() == []


def test_unexpected_output_fails_closed() -> None:
    with pytest.raises(RuntimeError, match="invalid rude JSON output"):
        clean.parse_findings("unexpected linter output")


def test_missing_paths_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="No Python files found"):
        clean.check_repository([str(tmp_path / "missing")])


def test_missing_configuration_fails_closed(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert clean.main(["--config", str(tmp_path / "missing.toml")]) == 2
    assert "config file not found" in capsys.readouterr().err


def test_real_rude_warning_fails_the_gate(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "violation.py"
    source.write_text("def f(a, b, c, d, e, f):\n    return a\n", encoding="utf-8")
    assert clean.main([str(source)]) == 1
    assert "CC102" in capsys.readouterr().out


def test_all_nine_clean_code_rules_are_discovered() -> None:
    from rude.core.rule_discovery import discover_rules

    codes = {rule.code for rule in discover_rules(select=["CC"])}
    assert codes == {
        "CC101",
        "CC102",
        "CC103",
        "CC104",
        "CC201",
        "CC202",
        "CC301",
        "CC302",
        "CC303",
    }


def test_subprocess_runner_rejects_tool_warnings(monkeypatch: pytest.MonkeyPatch) -> None:
    class Completed:
        returncode = 0
        stdout = ""
        stderr = "Plugin failed"

    monkeypatch.setattr(clean.subprocess, "run", lambda *args, **kwargs: Completed())
    with pytest.raises(RuntimeError, match="tool warning: Plugin failed"):
        clean.subprocess_runner(["rude"])
