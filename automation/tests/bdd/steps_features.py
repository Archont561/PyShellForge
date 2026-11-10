"""Steps for ``automation/features/feature_lint.feature``."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pytest_bdd import given, parsers, then, when

from automation.gherkin import lint

FEATURE = """Feature: Rendering a greeting

  Scenario: Render a greeting script
    Given a script that greets the user
    When I render the script
    Then the output greets the world
"""

OUT_OF_ORDER = """Feature: Rendering a greeting

  Scenario: Render a greeting script
    When I render the script
    Given a script that greets the user
    Then the output greets the world
"""

EMPTY = """Feature: Rendering a greeting
"""

STEPS: tuple[tuple[str, str], ...] = (
    ("given", "a script that greets the user"),
    ("when", "I render the script"),
    ("then", "the output greets the world"),
)

HEADER = (
    '"""Bound step definitions."""',
    "",
    "from pytest_bdd import given, then, when",
)


def _bound_steps(extra: tuple[str, str] | None = None) -> str:
    """Build a step-definition module without literal decorator text in-source."""
    lines = list(HEADER)
    entries = STEPS + ((extra,) if extra else ())
    for keyword, text in entries:
        lines += ["", "", f'@{keyword}("{text}")', "def _step():", "    pass"]
    return "\n".join(lines) + "\n"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@given("a feature file describing a shell rendering behaviour")
def feature_file(tmp_path: Path, context: dict[str, Any]) -> None:
    root = tmp_path / "repo"
    _write(root / "features" / "greeting.feature", FEATURE)
    (root / "tests" / "bdd").mkdir(parents=True, exist_ok=True)
    context["root"] = root


@given("a step definition for every step in the feature file")
def bound_steps(context: dict[str, Any]) -> None:
    _write(Path(str(context["root"])) / "tests" / "bdd" / "steps.py", _bound_steps())


@given("no step definitions")
def no_steps(context: dict[str, Any]) -> None:
    (Path(str(context["root"])) / "tests" / "bdd" / "steps.py").unlink(missing_ok=True)


@given("a step definition that no scenario uses")
def unused_step(context: dict[str, Any]) -> None:
    _write(
        Path(str(context["root"])) / "tests" / "bdd" / "steps.py",
        _bound_steps(("then", "a step nobody uses")),
    )


@given("a scenario whose Given step follows its When step")
def out_of_order(context: dict[str, Any]) -> None:
    root = Path(str(context["root"]))
    _write(root / "features" / "greeting.feature", OUT_OF_ORDER)
    _write(root / "tests" / "bdd" / "steps.py", _bound_steps())


@given("a feature file with a Feature statement but no scenarios")
def no_scenarios(context: dict[str, Any]) -> None:
    root = Path(str(context["root"]))
    _write(root / "features" / "greeting.feature", EMPTY)
    _write(root / "tests" / "bdd" / "steps.py", _bound_steps())


@when("I lint the features")
def lint_now(context: dict[str, Any]) -> None:
    root = Path(str(context["root"]))
    context["findings"] = lint.lint_features(root / "features", root / "tests" / "bdd", root=root)


@then("linting is clean")
def clean(context: dict[str, Any]) -> None:
    findings = context["findings"]
    assert findings == [], [finding.format() for finding in findings]


@then(parsers.parse("linting reports {code}"))
def reports(context: dict[str, Any], code: str) -> None:
    findings = context["findings"]
    codes = {finding.code for finding in findings}
    assert code in codes, sorted(codes)
