"""Tests for ``automation.detect_changes``."""

from __future__ import annotations

from pathlib import Path

import pytest

from automation import detect_changes as dc


@pytest.mark.parametrize(
    ("paths", "expected"),
    [
        (["docs/guides/getting-started.md"], ("docs", False)),
        (["README.md"], ("docs", False)),
        (["automation/readme/generate.py"], ("automation", False)),
        (["docs/README.md", "automation/docs/check.py"], ("docs+automation", False)),
        (["pyshellforge/src/pyshellforge/__init__.py"], ("product", True)),
        (["pyshellforge/pyproject.toml"], ("product", True)),
        ([".github/workflows/ci.yml"], ("product", True)),
        ([".github/ISSUE_TEMPLATE/bug_report.yml"], ("docs", False)),
        ([], ("no-diff", True)),
    ],
)
def test_classify(paths: list[str], expected: tuple[str, bool]) -> None:
    scope = dc.classify(paths, event="push")
    assert (scope.reason.split(":")[0], scope.full) == expected


def test_classify_reports_the_offending_product_path() -> None:
    scope = dc.classify(["README.md", "pyshellforge/src/pyshellforge/core/node.py"])
    assert scope.reason == "product:pyshellforge/src/pyshellforge/core/node.py"
    assert scope.full is True


@pytest.mark.parametrize("event", ["workflow_dispatch", "schedule"])
def test_manual_events_always_run_everything(event: str) -> None:
    scope = dc.classify(["docs/README.md"], event=event)
    assert (scope.docs, scope.automation, scope.full) == (True, True, True)


def test_issue_forms_are_docs_scope() -> None:
    scope = dc.classify([".github/ISSUE_TEMPLATE/feature_request.yml", "CHANGELOG.md"])
    assert (scope.docs, scope.automation, scope.full) == (True, False, False)


def test_automation_scenarios_are_automation_scope() -> None:
    scope = dc.classify(["automation/features/release_build.feature"])
    assert (scope.docs, scope.automation, scope.full) == (False, True, False)


def test_scope_as_outputs() -> None:
    outputs = dc.classify(["README.md"]).as_outputs()
    assert outputs == {
        "run_docs": "true",
        "run_automation": "false",
        "run_full": "false",
        "scope": "docs",
    }


def test_resolve_scope_uses_the_git_runner() -> None:
    def runner(command: list[str]) -> str:
        assert command[:3] == ["git", "diff", "--name-only"]
        return "docs/README.md\n"

    scope = dc.resolve_scope(base="abc123", head="def456", event="push", runner=runner)  # type: ignore[arg-type]
    assert scope.reason == "docs"


def test_resolve_scope_falls_back_to_full_for_initial_commits() -> None:
    scope = dc.resolve_scope(base="0" * 40, head="abc", event="push")
    assert scope.full is True


def test_resolve_scope_falls_back_to_full_without_a_base() -> None:
    assert dc.resolve_scope(base="", head="abc", event="push").full is True


def test_write_github_output(tmp_path: Path) -> None:
    destination = tmp_path / "output"
    dc.write_github_output({"run_docs": "true", "run_full": "false"}, str(destination))
    assert destination.read_text(encoding="utf-8") == "run_docs=true\nrun_full=false\n"


def test_write_github_output_is_a_noop_without_a_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GITHUB_OUTPUT", raising=False)
    dc.write_github_output({"run_docs": "true"})


def test_main_emits_outputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(dc, "resolve_scope", lambda **_: dc.Scope(True, False, False, "docs"))
    destination = tmp_path / "output"
    assert dc.main(["--github-output", "--head", "abc", "--base", "def"]) == 0
    monkeypatch.setenv("GITHUB_OUTPUT", str(destination))
    dc.main(["--github-output", "--head", "abc", "--base", "def"])
    assert "run_docs=true" in destination.read_text(encoding="utf-8")


def test_main_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(dc, "resolve_scope", lambda **_: dc.Scope(True, True, True, "product"))
    assert dc.main(["--json"]) == 0
    assert '"full": true' in capsys.readouterr().out


def test_main_survives_a_git_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    import subprocess

    def boom(**_: object) -> dc.Scope:
        raise subprocess.CalledProcessError(1, ["git", "diff"])

    monkeypatch.setattr(dc, "resolve_scope", boom)
    assert dc.main(["--base", "a", "--head", "b"]) == 0
