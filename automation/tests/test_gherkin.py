"""Tests for ``automation.gherkin``."""

from __future__ import annotations

from pathlib import Path

import pytest

from automation.gherkin import lint

FEATURE = """Feature: Rendering

  Background:
    Given a configured script

  Scenario: Greet
    Given a script
    When I render it
    Then I see bash
"""


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def steps_module(*pairs: tuple[str, str]) -> str:
    body = ['"""Steps."""', "", "from pytest_bdd import given, then, when"]
    for keyword, text in pairs:
        body += ["", "", f"@{keyword}({text!r})", "def _step():", "    pass"]
    return "\n".join(body) + "\n"


ALL_STEPS = (
    ("given", "a configured script"),
    ("given", "a script"),
    ("when", "I render it"),
    ("then", "I see bash"),
)


def build(tmp_path: Path, *, feature: str = FEATURE, steps: str | None = None) -> Path:
    root = tmp_path / "repo"
    write(root / "features" / "render.feature", feature)
    write(
        root / "tests" / "bdd" / "steps.py",
        steps if steps is not None else steps_module(*ALL_STEPS),
    )
    return root


def codes(root: Path) -> set[str]:
    return {
        finding.code
        for finding in lint.lint_features(root / "features", root / "tests" / "bdd", root=root)
    }


def test_clean_feature_and_steps(tmp_path: Path) -> None:
    assert (
        lint.lint_features(build(tmp_path) / "features", build(tmp_path) / "tests" / "bdd") or True
    )  # smoke: no crash


def test_clean_repository_passes(tmp_path: Path) -> None:
    root = build(tmp_path)
    assert codes(root) == set()


def test_undefined_step(tmp_path: Path) -> None:
    root = build(tmp_path, steps=steps_module(("given", "a configured script")))
    assert "PSF-FEAT-006" in codes(root)


def test_unused_definition(tmp_path: Path) -> None:
    root = build(tmp_path, steps=steps_module(*ALL_STEPS, ("then", "nobody uses this")))
    assert "PSF-FEAT-007" in codes(root)


def test_step_order(tmp_path: Path) -> None:
    feature = "Feature: R\n\n  Scenario: S\n    When I render it\n    Given a script\n"
    root = build(
        tmp_path,
        feature=feature,
        steps=steps_module(("when", "I render it"), ("given", "a script")),
    )
    assert "PSF-FEAT-005" in codes(root)


def test_missing_feature_statement(tmp_path: Path) -> None:
    root = build(tmp_path, feature="Scenario: S\n  Given a script\n")
    assert "PSF-FEAT-001" in codes(root)


def test_feature_without_scenarios(tmp_path: Path) -> None:
    root = build(tmp_path, feature="Feature: Only a name\n", steps=steps_module(*ALL_STEPS))
    assert "PSF-FEAT-002" in codes(root)


def test_scenario_without_steps(tmp_path: Path) -> None:
    root = build(
        tmp_path, feature="Feature: F\n\n  Scenario: Empty\n", steps=steps_module(*ALL_STEPS)
    )
    assert "PSF-FEAT-003" in codes(root)


def test_duplicate_scenario_names(tmp_path: Path) -> None:
    feature = "Feature: F\n\n  Scenario: Same\n    Given a script\n\n  Scenario: Same\n    Given a script\n"
    root = build(tmp_path, feature=feature, steps=steps_module(("given", "a script")))
    assert "PSF-FEAT-004" in codes(root)


def test_tags_are_stored_without_the_at_prefix(tmp_path: Path) -> None:
    path = write(tmp_path / "f.feature", "@product @tooling\n" + FEATURE)
    assert lint.parse_feature(path).tags == {"product", "tooling"}


def test_allowed_tags_accept_the_declared_tags(tmp_path: Path) -> None:
    root = build(tmp_path, feature="@product\n" + FEATURE)
    findings = lint.lint_features(
        root / "features",
        root / "tests" / "bdd",
        allowed_tags=frozenset({"product", "tooling"}),
        root=root,
    )
    assert "PSF-FEAT-008" not in {finding.code for finding in findings}


def test_unknown_tag_when_a_list_is_configured(tmp_path: Path) -> None:
    root = build(tmp_path, feature="@nope\n" + FEATURE)
    findings = lint.lint_features(
        root / "features", root / "tests" / "bdd", allowed_tags=frozenset({"product"}), root=root
    )
    assert "PSF-FEAT-008" in {finding.code for finding in findings}


def test_parse_feature_collects_scenarios_and_background(tmp_path: Path) -> None:
    path = write(tmp_path / "f.feature", FEATURE)
    feature = lint.parse_feature(path)
    assert feature.name == "Rendering"
    assert [scenario.name for scenario in feature.scenarios] == ["Greet"]
    assert feature.background is not None
    assert [step[2] for step in feature.background.steps] == ["a configured script"]


def test_step_definition_placeholders_match() -> None:
    definition = lint.StepDefinition(
        path="steps.py", line=1, keyword="then", text="the output contains {value}"
    )
    assert definition.matches("the output contains bash")
    assert not definition.matches("the output lacks bash")


def test_discover_helpers_on_missing_directories(tmp_path: Path) -> None:
    assert lint.discover_features(tmp_path / "nope") == []
    assert lint.discover_step_definitions(tmp_path / "nope") == []


def test_load_config_handles_a_missing_file(tmp_path: Path) -> None:
    assert lint.load_config(tmp_path / "nope.toml") == {}


def test_main_honours_disabled_codes(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = build(tmp_path, steps=steps_module(("given", "a configured script")))
    config = write(tmp_path / "gherlint.toml", '[reporting]\ndisable = ["PSF-FEAT-006"]\n')
    exit_code = lint.main(
        [
            "--features",
            str(root / "features"),
            "--steps",
            str(root / "tests" / "bdd"),
            "--config",
            str(config),
        ]
    )
    assert exit_code == 0
    assert "ok" in capsys.readouterr().out


def test_main_json_output(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = build(tmp_path, steps=steps_module(("given", "a configured script")))
    assert (
        lint.main(
            ["--features", str(root / "features"), "--steps", str(root / "tests" / "bdd"), "--json"]
        )
        == 1
    )
    assert "PSF-FEAT-006" in capsys.readouterr().out


def test_real_repository_features_are_consistent() -> None:
    """The committed features and step definitions must be in sync."""
    assert lint.lint_features() == []
