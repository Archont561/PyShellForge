"""Tests for ``automation.forms``."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from automation.forms import check

VALID = """name: Bug report
description: Something is wrong
title: "[Bug]: "
labels: ["bug"]
body:
  - type: markdown
    attributes:
      value: |
        Thanks for the report.
  - type: input
    id: version
    attributes:
      label: Version
    validations:
      required: true
"""

CONFIG = """blank_issues_enabled: false
contact_links:
  - name: Documentation
    url: https://example.com/docs
    about: Guides and reference.
"""


def build(
    root: Path, *, body: str = VALID, name: str = "bug_report.yml", config: str | None = None
) -> Path:
    """Write an issue-form directory into ``root`` and return it."""
    directory = root / check.TEMPLATE_DIR
    directory.mkdir(parents=True, exist_ok=True)
    (directory / name).write_text(body, encoding="utf-8")
    if config is not None:
        (directory / check.CONFIG_NAME).write_text(config, encoding="utf-8")
    return root


def codes(root: Path) -> set[str]:
    return {finding.code for finding in check.check_forms(root)}


def form(body: str, *, config: str | None = None) -> str:
    template = f"""name: Bug report
description: Something is wrong
body:
{body}"""
    return template


# -- structure -----------------------------------------------------------------
def test_a_valid_form_passes(tmp_path: Path) -> None:
    build(tmp_path)
    assert check.check_forms(tmp_path) == []


def test_missing_template_directory_is_reported(tmp_path: Path) -> None:
    assert codes(tmp_path) == {"PSF-FORM-001"}


def test_empty_template_directory_is_reported(tmp_path: Path) -> None:
    (tmp_path / check.TEMPLATE_DIR).mkdir(parents=True)
    assert codes(tmp_path) == {"PSF-FORM-002"}


def test_config_only_is_not_a_form(tmp_path: Path) -> None:
    build(tmp_path, body=CONFIG, name=check.CONFIG_NAME)
    assert codes(tmp_path) == {"PSF-FORM-002"}


def test_form_files_skips_the_config(tmp_path: Path) -> None:
    build(tmp_path, config=CONFIG)
    names = [path.name for path in check.form_files(tmp_path)]
    assert names == ["bug_report.yml"]
    assert check.CONFIG_NAME in [path.name for path in check.template_files(tmp_path)]


# -- top-level keys ------------------------------------------------------------
@pytest.mark.parametrize("key", ["name", "description"])
def test_missing_name_or_description(tmp_path: Path, key: str) -> None:
    body = VALID.replace(f"{key}: ", f"{key}_gone: ")
    build(tmp_path, body=body)
    assert "PSF-FORM-004" in codes(tmp_path)


def test_blank_name_is_reported(tmp_path: Path) -> None:
    build(tmp_path, body=VALID.replace("name: Bug report", 'name: "  "'))
    assert "PSF-FORM-004" in codes(tmp_path)


def test_missing_body_is_reported(tmp_path: Path) -> None:
    build(tmp_path, body="name: Bug\ndescription: Wrong\n")
    assert "PSF-FORM-005" in codes(tmp_path)


def test_empty_body_is_reported(tmp_path: Path) -> None:
    build(tmp_path, body="name: Bug\ndescription: Wrong\nbody: []\n")
    assert "PSF-FORM-005" in codes(tmp_path)


def test_labels_of_the_wrong_type(tmp_path: Path) -> None:
    build(tmp_path, body=VALID.replace('labels: ["bug"]', "labels: bug"))
    assert "PSF-FORM-014" in codes(tmp_path)


def test_title_of_the_wrong_type(tmp_path: Path) -> None:
    build(tmp_path, body=VALID.replace('title: "[Bug]: "', "title: [1, 2]"))
    assert "PSF-FORM-014" in codes(tmp_path)


def test_invalid_yaml_is_reported(tmp_path: Path) -> None:
    build(tmp_path, body="name: Bug\ndescription: [unclosed\n")
    assert "PSF-FORM-003" in codes(tmp_path)


def test_a_sequence_is_not_a_form(tmp_path: Path) -> None:
    build(tmp_path, body="- type: input\n")
    assert "PSF-FORM-003" in codes(tmp_path)


# -- elements ------------------------------------------------------------------
def test_unknown_element_type(tmp_path: Path) -> None:
    build(tmp_path, body=form("  - type: slider\n    id: x\n"))
    assert "PSF-FORM-007" in codes(tmp_path)


def test_element_without_type(tmp_path: Path) -> None:
    build(tmp_path, body=form("  - id: x\n"))
    assert "PSF-FORM-007" in codes(tmp_path)


def test_element_that_is_not_a_mapping(tmp_path: Path) -> None:
    build(tmp_path, body=form("  - just a string\n"))
    assert "PSF-FORM-006" in codes(tmp_path)


def test_missing_id(tmp_path: Path) -> None:
    build(tmp_path, body=form("  - type: input\n    attributes:\n      label: Version\n"))
    assert "PSF-FORM-008" in codes(tmp_path)


@pytest.mark.parametrize("element_id", ["with space", "with.dot", "", "id!"])
def test_malformed_id(tmp_path: Path, element_id: object) -> None:
    build(
        tmp_path,
        body=form(
            f'  - type: input\n    id: "{element_id}"\n    attributes:\n      label: Version\n'
        ),
    )
    assert "PSF-FORM-008" in codes(tmp_path)


def test_duplicate_ids(tmp_path: Path) -> None:
    body = form(
        "  - type: input\n    id: version\n    attributes:\n      label: One\n"
        "  - type: input\n    id: version\n    attributes:\n      label: Two\n"
    )
    build(tmp_path, body=body)
    findings = [
        finding for finding in check.check_forms(tmp_path) if finding.code == "PSF-FORM-008"
    ]
    assert len(findings) == 1
    assert "duplicate" in findings[0].message


def test_markdown_needs_a_value(tmp_path: Path) -> None:
    build(tmp_path, body=form("  - type: markdown\n    attributes: {}\n"))
    assert "PSF-FORM-009" in codes(tmp_path)


def test_markdown_must_not_declare_an_id(tmp_path: Path) -> None:
    build(
        tmp_path,
        body=form('  - type: markdown\n    id: intro\n    attributes:\n      value: "hi"\n'),
    )
    assert "PSF-FORM-017" in codes(tmp_path)


@pytest.mark.parametrize("kind", ["input", "textarea", "dropdown", "checkboxes", "upload"])
def test_labelled_elements_need_a_label(tmp_path: Path, kind: str) -> None:
    extra = ""
    if kind == "dropdown":
        extra = "\n      options:\n        - one\n"
    if kind == "checkboxes":
        extra = "\n      options:\n        - label: one\n"
    build(
        tmp_path,
        body=form(f"  - type: {kind}\n    id: field\n    attributes:\n      description: x{extra}"),
    )
    assert "PSF-FORM-010" in codes(tmp_path)


def test_dropdown_without_options(tmp_path: Path) -> None:
    build(
        tmp_path,
        body=form("  - type: dropdown\n    id: pick\n    attributes:\n      label: Pick\n"),
    )
    assert "PSF-FORM-011" in codes(tmp_path)


def test_dropdown_with_empty_options(tmp_path: Path) -> None:
    build(
        tmp_path,
        body=form(
            "  - type: dropdown\n    id: pick\n    attributes:\n      label: Pick\n      options: []\n"
        ),
    )
    assert "PSF-FORM-011" in codes(tmp_path)


def test_dropdown_options_must_be_distinct(tmp_path: Path) -> None:
    body = form(
        "  - type: dropdown\n    id: pick\n    attributes:\n      label: Pick\n"
        "      options:\n        - one\n        - one\n"
    )
    build(tmp_path, body=body)
    assert "PSF-FORM-016" in codes(tmp_path)


@pytest.mark.parametrize("multiple", ["maybe", 1])
def test_dropdown_multiple_must_be_boolean(tmp_path: Path, multiple: object) -> None:
    body = form(
        f"  - type: dropdown\n    id: pick\n    attributes:\n      label: Pick\n"
        f"      multiple: {multiple}\n      options:\n        - one\n        - two\n"
    )
    build(tmp_path, body=body)
    assert "PSF-FORM-016" in codes(tmp_path)


def test_dropdown_default_must_index_an_option(tmp_path: Path) -> None:
    body = form(
        "  - type: dropdown\n    id: pick\n    attributes:\n      label: Pick\n"
        "      default: 9\n      options:\n        - one\n        - two\n"
    )
    build(tmp_path, body=body)
    assert "PSF-FORM-016" in codes(tmp_path)


def test_dropdown_default_cannot_offer_none(tmp_path: Path) -> None:
    body = form(
        "  - type: dropdown\n    id: pick\n    attributes:\n      label: Pick\n"
        "      default: 0\n      options:\n        - None\n        - one\n"
    )
    build(tmp_path, body=body)
    assert "PSF-FORM-016" in codes(tmp_path)


def test_dropdown_with_a_valid_default_passes(tmp_path: Path) -> None:
    body = form(
        "  - type: dropdown\n    id: pick\n    attributes:\n      label: Pick\n"
        "      default: 1\n      options:\n        - one\n        - two\n"
    )
    build(tmp_path, body=body)
    assert check.check_forms(tmp_path) == []


def test_checkboxes_need_label_and_boolean_required(tmp_path: Path) -> None:
    body = form(
        "  - type: checkboxes\n    id: agree\n    attributes:\n      label: Agree\n"
        "      options:\n        - label: yes\n          required: sure\n"
    )
    build(tmp_path, body=body)
    assert "PSF-FORM-012" in codes(tmp_path)


def test_checkboxes_without_options(tmp_path: Path) -> None:
    build(
        tmp_path,
        body=form("  - type: checkboxes\n    id: agree\n    attributes:\n      label: Agree\n"),
    )
    assert "PSF-FORM-012" in codes(tmp_path)


def test_validations_required_must_be_boolean(tmp_path: Path) -> None:
    body = form(
        '  - type: input\n    id: v\n    attributes:\n      label: V\n    validations:\n      required: "yes"\n'
    )
    build(tmp_path, body=body)
    assert "PSF-FORM-013" in codes(tmp_path)


def test_min_length_is_allowed_on_input_and_textarea(tmp_path: Path) -> None:
    body = form(
        "  - type: textarea\n    id: repro\n    attributes:\n      label: Repro\n"
        "    validations:\n      required: true\n      min_length: 100\n"
    )
    build(tmp_path, body=body)
    assert check.check_forms(tmp_path) == []


def test_min_length_must_be_a_non_negative_integer(tmp_path: Path) -> None:
    body = form(
        "  - type: input\n    id: v\n    attributes:\n      label: V\n    validations:\n      min_length: -1\n"
    )
    build(tmp_path, body=body)
    assert "PSF-FORM-013" in codes(tmp_path)


@pytest.mark.parametrize("kind", ["dropdown", "markdown", "upload"])
def test_validations_are_not_allowed_on_every_type(tmp_path: Path, kind: str) -> None:
    extra = ""
    if kind == "dropdown":
        extra = "\n      options:\n        - one"
    if kind == "markdown":
        extra = '\n      value: "text"'
    body = form(
        f"  - type: {kind}\n    id: field\n    attributes:\n      label: Field{extra}\n"
        "    validations:\n      min_length: 3\n"
    )
    build(tmp_path, body=body)
    assert "PSF-FORM-013" in codes(tmp_path)


def test_unknown_validation_key(tmp_path: Path) -> None:
    body = form(
        "  - type: input\n    id: v\n    attributes:\n      label: V\n    validations:\n      pattern: x\n"
    )
    build(tmp_path, body=body)
    assert "PSF-FORM-013" in codes(tmp_path)


def test_attributes_of_the_wrong_type(tmp_path: Path) -> None:
    build(tmp_path, body=form("  - type: input\n    id: v\n    attributes: nope\n"))
    assert "PSF-FORM-006" in codes(tmp_path)


# -- config.yml ----------------------------------------------------------------
def test_a_valid_config_passes(tmp_path: Path) -> None:
    build(tmp_path, config=CONFIG)
    assert check.check_forms(tmp_path) == []


def test_blank_issues_must_be_boolean(tmp_path: Path) -> None:
    build(tmp_path, config='blank_issues_enabled: "no"\n')
    assert "PSF-FORM-015" in codes(tmp_path)


def test_contact_links_must_be_a_list(tmp_path: Path) -> None:
    build(tmp_path, config="contact_links: nope\n")
    assert "PSF-FORM-015" in codes(tmp_path)


@pytest.mark.parametrize("field", ["name", "url", "about"])
def test_contact_link_needs_every_field(tmp_path: Path, field: str) -> None:
    link = {"name": "Docs", "url": "https://example.com", "about": "Guides"}
    link.pop(field)
    config = "contact_links:\n" + "".join(f"  {key}: {value}\n" for key, value in link.items())
    build(tmp_path, config=config)
    assert "PSF-FORM-015" in codes(tmp_path)


def test_contact_link_url_must_be_absolute(tmp_path: Path) -> None:
    config = "contact_links:\n  - name: Docs\n    url: docs/README.md\n    about: Guides\n"
    build(tmp_path, config=config)
    assert "PSF-FORM-015" in codes(tmp_path)


def test_contact_link_entry_must_be_a_mapping(tmp_path: Path) -> None:
    build(tmp_path, config="contact_links:\n  - docs\n")
    assert "PSF-FORM-015" in codes(tmp_path)


def test_config_invalid_yaml(tmp_path: Path) -> None:
    build(tmp_path, config="contact_links: [\n")
    assert "PSF-FORM-003" in codes(tmp_path)


# -- reporting -----------------------------------------------------------------
def test_findings_carry_real_line_numbers(tmp_path: Path) -> None:
    body = form("  - type: input\n    id: v\n    attributes:\n      label: V\n  - type: slider\n")
    build(tmp_path, body=body)
    finding = next(item for item in check.check_forms(tmp_path) if item.code == "PSF-FORM-007")
    assert finding.line == 8
    assert finding.path == ".github/ISSUE_TEMPLATE/bug_report.yml"
    assert finding.format().startswith(".github/ISSUE_TEMPLATE/bug_report.yml:8: PSF-FORM-007")


def test_main_reports_success(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    build(tmp_path)
    assert check.main(["--root", str(tmp_path)]) == 0
    assert "forms: 1 form(s), ok" in capsys.readouterr().out


def test_main_reports_findings_as_json(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert check.main(["--root", str(tmp_path), "--json"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload[0]["code"] == "PSF-FORM-001"


def test_the_repository_forms_pass() -> None:
    """The forms that ship in this repository must satisfy the rules above."""
    assert check.check_forms(check.REPO_ROOT) == []
