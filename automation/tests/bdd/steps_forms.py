"""Steps for ``automation/features/issue_forms.feature``."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pytest_bdd import given, then, when

from automation.forms import check

HEADER = "name: Bug report\ndescription: Something is wrong\nbody:\n"


def _form(body: str) -> str:
    return HEADER + body


def _write(root: Path, text: str, name: str = "bug_report.yml") -> Path:
    directory = root / check.TEMPLATE_DIR
    directory.mkdir(parents=True, exist_ok=True)
    (directory / name).write_text(text, encoding="utf-8")
    return root


def _root(context: dict[str, Any], tmp_path: Path) -> Path:
    context["root"] = tmp_path
    return tmp_path


@given("an issue form with a name, a description and a body", target_fixture="root")
def form_with_a_body(context: dict[str, Any], tmp_path: Path) -> Path:
    body = (
        "  - type: textarea\n"
        "    id: definition\n"
        "    attributes:\n"
        "      label: Definition\n"
        "    validations:\n"
        "      required: true\n"
    )
    return _write(_root(context, tmp_path), _form(body))


@given("an issue form without a description", target_fixture="root")
def form_without_a_description(context: dict[str, Any], tmp_path: Path) -> Path:
    text = "name: Bug report\nbody:\n  - type: markdown\n    attributes:\n      value: hi\n"
    return _write(_root(context, tmp_path), text)


@given("an issue form with an element type of slider", target_fixture="root")
def form_with_an_unknown_type(context: dict[str, Any], tmp_path: Path) -> Path:
    return _write(_root(context, tmp_path), _form("  - type: slider\n    id: amount\n"))


@given("an issue form with a dropdown that has no options", target_fixture="root")
def form_with_an_empty_dropdown(context: dict[str, Any], tmp_path: Path) -> Path:
    body = "  - type: dropdown\n    id: shell\n    attributes:\n      label: Shell\n"
    return _write(_root(context, tmp_path), _form(body))


@given("an issue form with two elements that share an id", target_fixture="root")
def form_with_duplicate_ids(context: dict[str, Any], tmp_path: Path) -> Path:
    body = (
        "  - type: input\n    id: version\n    attributes:\n      label: Version\n"
        "  - type: input\n    id: version\n    attributes:\n      label: Series\n"
    )
    return _write(_root(context, tmp_path), _form(body))


@given("an issue form with a checkbox whose required flag is not a boolean", target_fixture="root")
def form_with_a_non_boolean_checkbox(context: dict[str, Any], tmp_path: Path) -> Path:
    body = (
        "  - type: checkboxes\n"
        "    id: confirm\n"
        "    attributes:\n"
        "      label: Confirm\n"
        "      options:\n"
        "        - label: I checked the docs\n"
        "          required: definitely\n"
    )
    return _write(_root(context, tmp_path), _form(body))


@given("a config file with a relative contact link", target_fixture="root")
def config_with_a_relative_link(context: dict[str, Any], tmp_path: Path) -> Path:
    valid = _form("  - type: markdown\n    attributes:\n      value: hi\n")
    config = (
        "blank_issues_enabled: false\n"
        "contact_links:\n"
        "  - name: Guides\n"
        "    url: docs/README.md\n"
        "    about: Read the guides first.\n"
    )
    return _write(_write(_root(context, tmp_path), valid), config, name=check.CONFIG_NAME)


@when("I validate the issue forms", target_fixture="findings")
def validate_the_forms(root: Path) -> list[check.Finding]:
    return check.check_forms(root)


@then("the issue forms are valid")
def forms_are_valid(findings: list[check.Finding]) -> None:
    assert findings == [], [finding.format() for finding in findings]


@then("form validation reports PSF-FORM-004")
def reports_missing_description(findings: list[check.Finding]) -> None:
    assert "PSF-FORM-004" in {finding.code for finding in findings}


@then("form validation reports PSF-FORM-007")
def reports_unknown_type(findings: list[check.Finding]) -> None:
    assert "PSF-FORM-007" in {finding.code for finding in findings}


@then("form validation reports PSF-FORM-008")
def reports_duplicate_id(findings: list[check.Finding]) -> None:
    assert "PSF-FORM-008" in {finding.code for finding in findings}


@then("form validation reports PSF-FORM-011")
def reports_empty_dropdown(findings: list[check.Finding]) -> None:
    assert "PSF-FORM-011" in {finding.code for finding in findings}


@then("form validation reports PSF-FORM-012")
def reports_bad_checkbox(findings: list[check.Finding]) -> None:
    assert "PSF-FORM-012" in {finding.code for finding in findings}


@then("form validation reports PSF-FORM-015")
def reports_bad_config(findings: list[check.Finding]) -> None:
    assert "PSF-FORM-015" in {finding.code for finding in findings}
