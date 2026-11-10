"""Steps for ``automation/features/clean_code.feature``."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

import pytest
from pytest_bdd import given, then, when

from automation.clean_code import check as clean

RECORD: dict[str, object] = {
    "file": "automation/demo.py",
    "line": 12,
    "column": 0,
    "code": "CC102",
    "message": "Function 'build' has too many parameters (8 > 5)",
    "severity": "warning",
}


@dataclass
class FakeLinter:
    """What the gate believes ``rude`` answered."""

    records: list[dict[str, object]] = field(default_factory=list)
    failure: str = ""

    def check_repository(self, *args: object, **kwargs: object) -> list[clean.Finding]:
        """Stand in for the real gate, which would shell out to ``rude``."""
        if self.failure:
            raise RuntimeError(self.failure)
        return clean.parse_findings("\n".join(json.dumps(record) for record in self.records))


def _run_gate(
    context: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    argv: list[str],
) -> None:
    monkeypatch.setattr(clean, "check_repository", context["linter"].check_repository)
    context["exit"] = clean.main(argv)
    context["output"] = capsys.readouterr()


@given("the linter answers with no findings")
def clean_tree(context: dict[str, Any]) -> None:
    context["linter"] = FakeLinter()


@given("the linter reports a function with too many parameters")
def one_finding(context: dict[str, Any]) -> None:
    context["linter"] = FakeLinter(records=[RECORD])


@given("the linter cannot be started")
def broken_linter(context: dict[str, Any]) -> None:
    context["linter"] = FakeLinter(failure="rude exited with status 3: not installed")


@when("I run the clean code gate")
def run_gate(
    context: dict[str, Any], monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _run_gate(context, monkeypatch, capsys, [])


@when("I run the clean code gate with JSON output")
def run_gate_json(
    context: dict[str, Any], monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _run_gate(context, monkeypatch, capsys, ["--json"])


@then("the gate succeeds")
def gate_succeeds(context: dict[str, Any]) -> None:
    assert context["exit"] == 0


@then("the gate fails")
def gate_fails(context: dict[str, Any]) -> None:
    assert context["exit"] == 1


@then("the gate fails with a tool error")
def gate_tool_error(context: dict[str, Any]) -> None:
    assert context["exit"] == 2


@then("the output reports the trees are clean")
def output_clean(context: dict[str, Any]) -> None:
    assert "ok" in context["output"].out


@then("the output names the rule that reported")
def output_names_rule(context: dict[str, Any]) -> None:
    assert "CC102" in context["output"].out
    assert "CC102" in context["output"].err


@then("the output explains that the linter failed")
def output_explains_failure(context: dict[str, Any]) -> None:
    assert "clean-code:" in context["output"].err


@then("the output is a list of findings")
def output_is_json(context: dict[str, Any]) -> None:
    findings = json.loads(context["output"].out)
    assert findings[0]["path"] == "automation/demo.py"
    assert findings[0]["code"] == "CC102"
