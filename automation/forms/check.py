"""Validate the GitHub Issue Forms in ``.github/ISSUE_TEMPLATE/``.

GitHub renders an Issue Form from YAML, and it fails quietly: an unknown
``type``, a missing ``id`` or a ``dropdown`` without ``options`` produces a form
that either will not open or loses a field, and you only find out when a
contributor tries to report a bug. This script checks the schema offline, in the
same way ``automation.docs`` checks the documentation tree.

The rules implemented here are the ones from GitHub's issue-form syntax that can
be checked without the network:

* ``name``, ``description`` and a non-empty ``body`` are required;
* every element has a known ``type`` from ``markdown``, ``input``, ``textarea``,
  ``dropdown``, ``checkboxes`` and ``upload``;
* every element except ``markdown`` has a unique, well-formed ``id``;
* ``markdown`` carries its text in ``attributes.value``;
* ``input``/``textarea`` carry ``attributes.label``;
* ``dropdown`` offers a non-empty list of options, ``checkboxes`` a list of
  ``{label, required}`` entries;
* ``validations.required`` is a boolean and only appears where GitHub accepts it;
* ``config.yml`` keeps ``blank_issues_enabled`` boolean and every ``contact_links``
  entry complete.

Preview is a separate, manual step: ``gh form preview`` serves the template as
HTML from the GitHub CLI extension
[``gh-form``](https://github.com/yudai-nkt/gh-form), which needs ``gh``, an
authenticated session and network access, so it is never part of CI.

Usage::

    python -m automation.forms            # human-readable findings, non-zero on error
    python -m automation.forms --json     # machine-readable findings
"""

from __future__ import annotations

import argparse
import json
import re
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml

#: Repository root, derived from this file (``automation/forms/check.py``).
REPO_ROOT = Path(__file__).resolve().parents[2]

#: Where GitHub looks for issue forms and their configuration.
TEMPLATE_DIR = Path(".github") / "ISSUE_TEMPLATE"

#: The configuration file, which is not a form.
CONFIG_NAME = "config.yml"

#: Element types GitHub understands.
ELEMENT_TYPES: tuple[str, ...] = (
    "markdown",
    "input",
    "textarea",
    "dropdown",
    "checkboxes",
    "upload",
)

#: Types that must carry an ``id``.
ID_TYPES: frozenset[str] = frozenset({"input", "textarea", "dropdown", "checkboxes", "upload"})

#: Types that accept ``validations``.
VALIDATED_TYPES: frozenset[str] = frozenset({"input", "textarea", "dropdown", "checkboxes"})

#: Validation keys each type accepts.
VALIDATION_KEYS: dict[str, frozenset[str]] = {
    "input": frozenset({"required", "min_length"}),
    "textarea": frozenset({"required", "min_length"}),
    "dropdown": frozenset({"required"}),
    "checkboxes": frozenset({"required"}),
}

#: Types that render a labelled field.
LABELLED_TYPES: frozenset[str] = frozenset(
    {"input", "textarea", "dropdown", "checkboxes", "upload"}
)

#: GitHub requires ids to be alphanumeric plus ``-`` and ``_``.
ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")

#: Codes are stable; documentation and tests quote them.
CODES: dict[str, str] = {
    "PSF-FORM-001": "issue template directory is missing",
    "PSF-FORM-002": "no issue forms found",
    "PSF-FORM-003": "template is not valid YAML or not a mapping",
    "PSF-FORM-004": "template has no name or description",
    "PSF-FORM-005": "template has no body elements",
    "PSF-FORM-006": "body element is not a mapping",
    "PSF-FORM-007": "body element has an unknown or missing type",
    "PSF-FORM-008": "element is missing a well-formed or unique id",
    "PSF-FORM-009": "markdown element has no attributes.value",
    "PSF-FORM-010": "input or textarea element has no attributes.label",
    "PSF-FORM-011": "dropdown has no usable options",
    "PSF-FORM-012": "checkboxes options are not {label, required} mappings",
    "PSF-FORM-013": "validations.required is not a boolean or is not allowed here",
    "PSF-FORM-014": "labels, assignees or title have the wrong type",
    "PSF-FORM-015": "config.yml keeps an invalid blank_issues_enabled or contact_links entry",
    "PSF-FORM-016": "dropdown options repeat, or default/multiple are invalid",
    "PSF-FORM-017": "markdown element must not declare an id",
}


@dataclass(frozen=True, order=True)
class Finding:
    """One defect in the issue templates."""

    path: str
    line: int
    code: str
    message: str

    def format(self) -> str:
        """Render as ``path:line: CODE message``."""
        return f"{self.path}:{self.line}: {self.code} {self.message}"

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serialisable representation."""
        return asdict(self)


def _mapping_node(text: str) -> yaml.MappingNode | None:
    try:
        node = yaml.compose(text, Loader=yaml.SafeLoader)
    except yaml.YAMLError:
        return None
    return node if isinstance(node, yaml.MappingNode) else None


def _value_node(mapping: yaml.MappingNode | None, key: str) -> yaml.Node | None:
    if mapping is None:
        return None
    for name, value in mapping.value:
        if isinstance(name, yaml.ScalarNode) and name.value == key:
            return value
    return None


def sequence_lines(text: str, key: str) -> list[int]:
    """Return the 1-based line of each item of the top-level sequence ``key``."""
    node = _value_node(_mapping_node(text), key)
    if not isinstance(node, yaml.SequenceNode):
        return []
    return [item.start_mark.line + 1 for item in node.value]


def key_line(text: str, key: str) -> int:
    """Return the 1-based line of a top-level ``key``, or 1."""
    mapping = _mapping_node(text)
    if mapping is None:
        return 1
    for name, _value in mapping.value:
        if isinstance(name, yaml.ScalarNode) and name.value == key:
            return name.start_mark.line + 1
    return 1


def _relative(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def template_files(root: Path) -> list[Path]:
    """Return the issue-form files in ``root``, config first, in a stable order."""
    directory = root / TEMPLATE_DIR
    if not directory.is_dir():
        return []
    files = sorted(path for path in directory.iterdir() if path.suffix in {".yml", ".yaml"})
    return sorted(files, key=lambda path: (path.name != CONFIG_NAME, path.name))


def form_files(root: Path) -> list[Path]:
    """Return the templates that are forms, that is everything but ``config.yml``."""
    return [path for path in template_files(root) if path.name != CONFIG_NAME]


def _is_string_list(value: Any) -> bool:
    """Whether ``value`` is a list whose items are all strings."""
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def _check_text_keys(relative: str, text: str, data: dict[str, Any]) -> list[Finding]:
    """Check the two keys a form cannot do without: ``name`` and ``description``."""
    findings: list[Finding] = []
    for key in ("name", "description"):
        value = data.get(key)
        if not isinstance(value, str) or not value.strip():
            findings.append(
                Finding(
                    relative,
                    key_line(text, key),
                    "PSF-FORM-004",
                    f"`{key}` must be a non-empty string",
                )
            )
    return findings


def _check_optional_keys(relative: str, text: str, data: dict[str, Any]) -> list[Finding]:
    """Check the optional keys, which are still typed when a form declares them."""
    findings: list[Finding] = []
    if "title" in data and not isinstance(data["title"], str):
        findings.append(
            Finding(relative, key_line(text, "title"), "PSF-FORM-014", "`title` must be a string")
        )
    for key in ("labels", "assignees"):
        if key in data and not _is_string_list(data[key]):
            findings.append(
                Finding(
                    relative,
                    key_line(text, key),
                    "PSF-FORM-014",
                    f"`{key}` must be a list of strings",
                )
            )
    return findings


def _check_body_elements(relative: str, text: str, body: Sequence[Any]) -> list[Finding]:
    """Check every element of a form body, carrying the ids seen so far."""
    lines = sequence_lines(text, "body")
    seen: set[str] = set()
    findings: list[Finding] = []
    for index, element in enumerate(body):
        line = lines[index] if index < len(lines) else 1
        findings.extend(_check_element(relative, line, element, seen))
    return findings


def check_template(path: Path, root: Path) -> list[Finding]:
    """Validate one issue form."""
    relative = _relative(path, root)
    text = path.read_text(encoding="utf-8")

    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as error:
        return [Finding(relative, 1, "PSF-FORM-003", f"YAML could not be parsed: {error}")]
    if not isinstance(data, dict):
        return [Finding(relative, 1, "PSF-FORM-003", "a template must be a YAML mapping")]

    findings = [
        *_check_text_keys(relative, text, data),
        *_check_optional_keys(relative, text, data),
    ]
    body = data.get("body")
    if not isinstance(body, list) or not body:
        findings.append(
            Finding(
                relative, key_line(text, "body"), "PSF-FORM-005", "`body` must be a non-empty list"
            )
        )
        return findings
    findings.extend(_check_body_elements(relative, text, body))
    return findings


def _check_id(
    relative: str, line: int, kind: Any, element_id: Any, seen: set[str]
) -> list[Finding]:
    """Check that an element id is well formed and unique within the form."""
    if not isinstance(element_id, str) or not ID_RE.match(element_id):
        return [
            Finding(
                relative,
                line,
                "PSF-FORM-008",
                f"a {kind!r} element needs an `id` of letters, digits, `-` or `_`",
            )
        ]
    if element_id in seen:
        return [Finding(relative, line, "PSF-FORM-008", f"duplicate element id {element_id!r}")]
    seen.add(element_id)
    return []


def _check_identity(
    relative: str, line: int, kind: Any, element: dict[str, Any], seen: set[str]
) -> list[Finding]:
    """Check the id rules: markdown takes none, the labelled types take a unique one."""
    findings: list[Finding] = []
    if kind == "markdown" and "id" in element:
        findings.append(
            Finding(
                relative,
                line,
                "PSF-FORM-017",
                "a 'markdown' element is not submitted, so it must not declare an `id`",
            )
        )
    if kind in ID_TYPES:
        findings.extend(_check_id(relative, line, kind, element.get("id"), seen))
    return findings


def _check_attributes(
    relative: str, line: int, kind: Any, attributes: dict[str, Any]
) -> list[Finding]:
    """Check the text an element shows: markdown has a value, the rest a label."""
    if kind == "markdown":
        value = attributes.get("value")
        if not isinstance(value, str) or not value.strip():
            return [
                Finding(
                    relative, line, "PSF-FORM-009", "a 'markdown' element needs `attributes.value`"
                )
            ]
        return []
    if kind in LABELLED_TYPES:
        label = attributes.get("label")
        if not isinstance(label, str) or not label.strip():
            return [
                Finding(
                    relative, line, "PSF-FORM-010", f"a {kind!r} element needs `attributes.label`"
                )
            ]
    return []


def _check_options(
    relative: str, line: int, kind: Any, attributes: dict[str, Any]
) -> list[Finding]:
    """Check the option lists of a dropdown and of a checkboxes element."""
    if kind == "dropdown":
        options = attributes.get("options")
        if isinstance(options, list) and _valid_options(options):
            return _check_dropdown(relative, line, attributes, options)
        return [
            Finding(
                relative,
                line,
                "PSF-FORM-011",
                "a 'dropdown' element needs a non-empty `options` list",
            )
        ]
    if kind == "checkboxes" and not _valid_checkboxes(attributes.get("options")):
        return [
            Finding(
                relative,
                line,
                "PSF-FORM-012",
                "a 'checkboxes' element needs `options` entries with a `label` and an optional boolean `required`",
            )
        ]
    return []


def _check_min_length(relative: str, line: int, min_length: Any) -> list[Finding]:
    """Check ``validations.min_length`` when the element declares one."""
    if min_length is None or (
        isinstance(min_length, int) and not isinstance(min_length, bool) and min_length >= 0
    ):
        return []
    return [
        Finding(
            relative,
            line,
            "PSF-FORM-013",
            "`validations.min_length` must be a non-negative integer",
        )
    ]


def _check_validation_keys(
    relative: str, line: int, kind: Any, validations: dict[str, Any]
) -> list[Finding]:
    """Check that the element type accepts validations, and only the keys it knows."""
    if kind not in VALIDATED_TYPES:
        return [
            Finding(
                relative, line, "PSF-FORM-013", f"a {kind!r} element does not accept `validations`"
            )
        ]
    unknown = set(validations) - VALIDATION_KEYS.get(kind, frozenset())
    if unknown:
        return [
            Finding(
                relative,
                line,
                "PSF-FORM-013",
                f"unknown validation key(s): {', '.join(sorted(unknown))}",
            )
        ]
    return []


def _check_validations(relative: str, line: int, kind: Any, validations: Any) -> list[Finding]:
    """Check the ``validations`` block of an element."""
    if validations is None:
        return []
    if not isinstance(validations, dict):
        return [Finding(relative, line, "PSF-FORM-013", "`validations` must be a mapping")]

    findings: list[Finding] = []
    required = validations.get("required")
    if required is not None and not isinstance(required, bool):
        findings.append(
            Finding(relative, line, "PSF-FORM-013", "`validations.required` must be a boolean")
        )
    findings.extend(_check_min_length(relative, line, validations.get("min_length")))
    findings.extend(_check_validation_keys(relative, line, kind, validations))
    return findings


def _check_element(relative: str, line: int, element: Any, seen: set[str]) -> list[Finding]:
    """Check one body element: its type, its id, its text, its options, its validations."""
    if not isinstance(element, dict):
        return [Finding(relative, line, "PSF-FORM-006", "each body element must be a mapping")]

    kind = element.get("type")
    if kind not in ELEMENT_TYPES:
        return [
            Finding(
                relative,
                line,
                "PSF-FORM-007",
                f"`type` must be one of {', '.join(ELEMENT_TYPES)}, found {kind!r}",
            )
        ]

    findings: list[Finding] = []
    attributes = element.get("attributes")
    if attributes is not None and not isinstance(attributes, dict):
        findings.append(
            Finding(
                relative,
                line,
                "PSF-FORM-006",
                f"`attributes` of a {kind!r} element must be a mapping",
            )
        )
        attributes = {}
    attributes = attributes or {}

    findings.extend(_check_identity(relative, line, kind, element, seen))
    findings.extend(_check_attributes(relative, line, kind, attributes))
    findings.extend(_check_options(relative, line, kind, attributes))
    findings.extend(_check_validations(relative, line, kind, element.get("validations")))
    return findings


def _check_dropdown(
    relative: str, line: int, attributes: dict[str, Any], options: list[Any]
) -> list[Finding]:
    findings: list[Finding] = []
    labels = [option if isinstance(option, str) else option.get("label") for option in options]
    if len(set(labels)) != len(labels):
        findings.append(
            Finding(relative, line, "PSF-FORM-016", "dropdown options must all be distinct")
        )
    multiple = attributes.get("multiple")
    if multiple is not None and not isinstance(multiple, bool):
        findings.append(
            Finding(relative, line, "PSF-FORM-016", "`attributes.multiple` must be a boolean")
        )
    default = attributes.get("default")
    if default is not None:
        if (
            not isinstance(default, int)
            or isinstance(default, bool)
            or not 0 <= default < len(options)
        ):
            findings.append(
                Finding(
                    relative,
                    line,
                    "PSF-FORM-016",
                    "`attributes.default` must be the index of an option",
                )
            )
        elif any(str(label).strip().lower() in {"none", "n/a"} for label in labels):
            findings.append(
                Finding(
                    relative,
                    line,
                    "PSF-FORM-016",
                    "a dropdown with `default` cannot offer 'None' or 'n/a'",
                )
            )
    return findings


def _valid_options(options: Any) -> bool:
    if not isinstance(options, list) or not options:
        return False
    return all(
        isinstance(option, str)
        or (isinstance(option, dict) and isinstance(option.get("label"), str))
        for option in options
    )


def _valid_checkboxes(options: Any) -> bool:
    if not isinstance(options, list) or not options:
        return False
    for option in options:
        if not isinstance(option, dict) or not isinstance(option.get("label"), str):
            return False
        if "required" in option and not isinstance(option["required"], bool):
            return False
    return True


def _check_blank_issues(relative: str, text: str, data: dict[str, Any]) -> list[Finding]:
    """Check ``blank_issues_enabled``, which is optional and boolean."""
    blank = data.get("blank_issues_enabled")
    if blank is not None and not isinstance(blank, bool):
        return [
            Finding(
                relative,
                key_line(text, "blank_issues_enabled"),
                "PSF-FORM-015",
                "`blank_issues_enabled` must be a boolean",
            )
        ]
    return []


def _check_contact_link(relative: str, line: int, link: Any) -> list[Finding]:
    """Check one contact link: its mapping, its three fields and its absolute url."""
    if not isinstance(link, dict):
        return [Finding(relative, line, "PSF-FORM-015", "each contact link must be a mapping")]
    findings = [
        Finding(relative, line, "PSF-FORM-015", f"the contact link is missing `{field}`")
        for field in ("name", "url", "about")
        if not isinstance(link.get(field), str) or not str(link.get(field)).strip()
    ]
    url = link.get("url")
    if isinstance(url, str) and not url.startswith(("https://", "http://")):
        findings.append(
            Finding(relative, line, "PSF-FORM-015", f"contact link url must be absolute: {url!r}")
        )
    return findings


def _check_contact_links(relative: str, text: str, data: dict[str, Any]) -> list[Finding]:
    """Check the ``contact_links`` list, link by link."""
    links = data.get("contact_links")
    if links is None:
        return []
    if not isinstance(links, list):
        return [
            Finding(
                relative,
                key_line(text, "contact_links"),
                "PSF-FORM-015",
                "`contact_links` must be a list",
            )
        ]
    lines = sequence_lines(text, "contact_links")
    findings: list[Finding] = []
    for index, link in enumerate(links):
        line = lines[index] if index < len(lines) else 1
        findings.extend(_check_contact_link(relative, line, link))
    return findings


def check_config(path: Path, root: Path) -> list[Finding]:
    """Validate ``config.yml``."""
    relative = _relative(path, root)
    text = path.read_text(encoding="utf-8")
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as error:
        return [Finding(relative, 1, "PSF-FORM-003", f"YAML could not be parsed: {error}")]
    if not isinstance(data, dict):
        return [Finding(relative, 1, "PSF-FORM-003", "config.yml must be a YAML mapping")]

    return [*_check_blank_issues(relative, text, data), *_check_contact_links(relative, text, data)]


def check_forms(root: Path = REPO_ROOT) -> list[Finding]:
    """Validate every issue form under ``root``."""
    root = Path(root)
    directory = root / TEMPLATE_DIR
    if not directory.is_dir():
        return [
            Finding(
                TEMPLATE_DIR.as_posix(),
                1,
                "PSF-FORM-001",
                "the issue template directory is missing",
            )
        ]

    forms = form_files(root)
    if not forms:
        return [
            Finding(
                TEMPLATE_DIR.as_posix(),
                1,
                "PSF-FORM-002",
                "no issue forms were found",
            )
        ]

    findings: list[Finding] = []
    for path in forms:
        findings.extend(check_template(path, root))
    config = directory / CONFIG_NAME
    if config.is_file():
        findings.extend(check_config(config, root))
    return sorted(findings)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point: print findings, exit non-zero when any exist."""
    parser = argparse.ArgumentParser(
        prog="python -m automation.forms",
        description="Validate the GitHub Issue Forms in .github/ISSUE_TEMPLATE/.",
    )
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help="repository root")
    parser.add_argument("--json", action="store_true", help="emit JSON findings")
    args = parser.parse_args(argv)

    findings = check_forms(args.root)
    if args.json:
        print(json.dumps([finding.to_dict() for finding in findings], indent=2))
    else:
        for finding in findings:
            print(finding.format())
        count = len(form_files(args.root))
        status = "ok" if not findings else f"{len(findings)} finding(s)"
        print(f"forms: {count} form(s), {status}")
    return 1 if findings else 0


if __name__ == "__main__":  # pragma: no cover - module entry point
    raise SystemExit(main())
