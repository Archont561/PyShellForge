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


def check_template(path: Path, root: Path) -> list[Finding]:
    """Validate one issue form."""
    relative = _relative(path, root)
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []

    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as error:
        return [Finding(relative, 1, "PSF-FORM-003", f"YAML could not be parsed: {error}")]
    if not isinstance(data, dict):
        return [Finding(relative, 1, "PSF-FORM-003", "a template must be a YAML mapping")]

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

    if "title" in data and not isinstance(data["title"], str):
        findings.append(
            Finding(relative, key_line(text, "title"), "PSF-FORM-014", "`title` must be a string")
        )
    for key in ("labels", "assignees"):
        if key in data and not (
            isinstance(data[key], list) and all(isinstance(item, str) for item in data[key])
        ):
            findings.append(
                Finding(
                    relative,
                    key_line(text, key),
                    "PSF-FORM-014",
                    f"`{key}` must be a list of strings",
                )
            )

    body = data.get("body")
    if not isinstance(body, list) or not body:
        findings.append(
            Finding(
                relative, key_line(text, "body"), "PSF-FORM-005", "`body` must be a non-empty list"
            )
        )
        return findings

    lines = sequence_lines(text, "body")
    seen: set[str] = set()
    for index, element in enumerate(body):
        line = lines[index] if index < len(lines) else 1
        findings.extend(_check_element(relative, line, element, seen))
    return findings


def _check_element(relative: str, line: int, element: Any, seen: set[str]) -> list[Finding]:
    findings: list[Finding] = []
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
        element_id = element.get("id")
        if not isinstance(element_id, str) or not ID_RE.match(element_id):
            findings.append(
                Finding(
                    relative,
                    line,
                    "PSF-FORM-008",
                    f"a {kind!r} element needs an `id` of letters, digits, `-` or `_`",
                )
            )
        elif element_id in seen:
            findings.append(
                Finding(relative, line, "PSF-FORM-008", f"duplicate element id {element_id!r}")
            )
        else:
            seen.add(element_id)

    attributes = attributes or {}
    if kind == "markdown":
        value = attributes.get("value")
        if not isinstance(value, str) or not value.strip():
            findings.append(
                Finding(
                    relative, line, "PSF-FORM-009", "a 'markdown' element needs `attributes.value`"
                )
            )
    elif kind in LABELLED_TYPES:
        label = attributes.get("label")
        if not isinstance(label, str) or not label.strip():
            findings.append(
                Finding(
                    relative, line, "PSF-FORM-010", f"a {kind!r} element needs `attributes.label`"
                )
            )

    if kind == "dropdown":
        options = attributes.get("options")
        if isinstance(options, list) and _valid_options(options):
            findings.extend(_check_dropdown(relative, line, attributes, options))
        else:
            findings.append(
                Finding(
                    relative,
                    line,
                    "PSF-FORM-011",
                    "a 'dropdown' element needs a non-empty `options` list",
                )
            )
    if kind == "checkboxes" and not _valid_checkboxes(attributes.get("options")):
        findings.append(
            Finding(
                relative,
                line,
                "PSF-FORM-012",
                "a 'checkboxes' element needs `options` entries with a `label` and an optional boolean `required`",
            )
        )

    validations = element.get("validations")
    if validations is not None:
        if not isinstance(validations, dict):
            findings.append(
                Finding(relative, line, "PSF-FORM-013", "`validations` must be a mapping")
            )
        else:
            required = validations.get("required")
            if required is not None and not isinstance(required, bool):
                findings.append(
                    Finding(
                        relative, line, "PSF-FORM-013", "`validations.required` must be a boolean"
                    )
                )
            min_length = validations.get("min_length")
            if min_length is not None and (
                not isinstance(min_length, int) or isinstance(min_length, bool) or min_length < 0
            ):
                findings.append(
                    Finding(
                        relative,
                        line,
                        "PSF-FORM-013",
                        "`validations.min_length` must be a non-negative integer",
                    )
                )
            unknown = set(validations) - VALIDATION_KEYS.get(kind, frozenset())
            if kind not in VALIDATED_TYPES:
                findings.append(
                    Finding(
                        relative,
                        line,
                        "PSF-FORM-013",
                        f"a {kind!r} element does not accept `validations`",
                    )
                )
            elif unknown:
                findings.append(
                    Finding(
                        relative,
                        line,
                        "PSF-FORM-013",
                        f"unknown validation key(s): {', '.join(sorted(unknown))}",
                    )
                )
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

    findings: list[Finding] = []
    blank = data.get("blank_issues_enabled")
    if blank is not None and not isinstance(blank, bool):
        findings.append(
            Finding(
                relative,
                key_line(text, "blank_issues_enabled"),
                "PSF-FORM-015",
                "`blank_issues_enabled` must be a boolean",
            )
        )

    links = data.get("contact_links")
    if links is not None:
        if not isinstance(links, list):
            findings.append(
                Finding(
                    relative,
                    key_line(text, "contact_links"),
                    "PSF-FORM-015",
                    "`contact_links` must be a list",
                )
            )
        else:
            lines = sequence_lines(text, "contact_links")
            for index, link in enumerate(links):
                line = lines[index] if index < len(lines) else 1
                if not isinstance(link, dict):
                    findings.append(
                        Finding(
                            relative, line, "PSF-FORM-015", "each contact link must be a mapping"
                        )
                    )
                    continue
                for field in ("name", "url", "about"):
                    if not isinstance(link.get(field), str) or not str(link.get(field)).strip():
                        findings.append(
                            Finding(
                                relative,
                                line,
                                "PSF-FORM-015",
                                f"the contact link is missing `{field}`",
                            )
                        )
                url = link.get("url")
                if isinstance(url, str) and not url.startswith(("https://", "http://")):
                    findings.append(
                        Finding(
                            relative,
                            line,
                            "PSF-FORM-015",
                            f"contact link url must be absolute: {url!r}",
                        )
                    )
    return findings


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
