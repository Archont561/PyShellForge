"""Lint Gherkin feature files and check that every step has a definition.

The repository describes behaviour in ``*.feature`` files and binds it to
``pytest-bdd`` step definitions. This module keeps the two in sync and enforces
the house style for scenarios. Scenarios live beside the code they describe:
``automation/features/`` for the automation, ``pyshellforge/features/`` for the
product once it has any, with the step definitions under the matching ``tests/``.

It is a strict, offline counterpart to
`gherlint <https://pypi.org/project/gherlint/>`_ (configured in
``gherlint.toml``): run either one, or both in CI.

Usage::

    python -m automation.gherkin            # every feature tree, every step module
    python -m automation.gherkin --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

FEATURE = re.compile(r"^Feature:\s*(?P<name>\S.*?)\s*$")
SCENARIO = re.compile(
    r"^(?:Scenario Outline|Scenario Template|Scenario|Example):\s*(?P<name>\S.*?)\s*$"
)
STEP = re.compile(r"^(?P<keyword>Given|When|Then|And|But|\*)\s+(?P<text>\S.*?)\s*$")
STEP_DEFINITION = re.compile(
    r"@(?:given|when|then)\(\s*(?:parsers\.\w+\(\s*)?[\"'](?P<text>.+?)[\"']", re.S
)
PLACEHOLDER = re.compile(r"\{\w+\}|<[^>]+>")
TAG = re.compile(r"^\s*(@[\w:.-]+(?:\s+@[\w:.-]+)*)\s*$")

#: Where the Gherkin scenarios and their step definitions live: beside the code
#: they describe, which is why there is one pair per tree. Missing directories are
#: tolerated, so the product tree may appear later.
FEATURES_DIRS: tuple[Path, ...] = (
    REPO_ROOT / "automation" / "features",
    REPO_ROOT / "pyshellforge" / "features",
)
STEPS_DIRS: tuple[Path, ...] = (
    REPO_ROOT / "automation" / "tests" / "bdd",
    REPO_ROOT / "pyshellforge" / "tests" / "bdd",
)

#: Order of the narrative phases; ``And``/``But``/``*`` inherit the previous one.
PHASES = {"Given": 0, "When": 1, "Then": 2}

CODES: dict[str, str] = {
    "PSF-FEAT-001": "feature file has no Feature: statement",
    "PSF-FEAT-002": "feature file has no scenarios",
    "PSF-FEAT-003": "scenario has no steps",
    "PSF-FEAT-004": "duplicate scenario name in the same feature file",
    "PSF-FEAT-005": "step appears in the wrong order (Given, When, Then)",
    "PSF-FEAT-006": "step has no matching step definition",
    "PSF-FEAT-007": "step definition is not used by any scenario",
    "PSF-FEAT-008": "unknown tag",
}


@dataclass(frozen=True, order=True)
class Finding:
    """One Gherkin defect."""

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


@dataclass
class Scenario:
    """A scenario and its steps."""

    name: str
    line: int
    steps: list[tuple[int, str, str]] = field(default_factory=list)


@dataclass
class Feature:
    """A parsed feature file."""

    path: Path
    line: int
    name: str
    scenarios: list[Scenario] = field(default_factory=list)
    background: Scenario | None = None
    tags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class StepDefinition:
    """A bound step definition."""

    path: str
    line: int
    keyword: str
    text: str

    def matches(self, text: str) -> bool:
        """Whether ``text`` binds to this definition."""
        pattern = PLACEHOLDER.sub("\x00", self.text)
        regex = ".+?".join(re.escape(part) for part in pattern.split("\x00"))
        return re.fullmatch(regex, text) is not None


def parse_feature(path: Path) -> Feature:
    """Parse a ``.feature`` file into a :class:`Feature`."""
    feature = Feature(path=path, line=0, name="")
    current: Scenario | None = None
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if match := FEATURE.match(line):
            if not feature.name:
                feature.line = number
            feature.name = match.group("name")
            current = None
            continue
        if line.startswith("Background:"):
            current = Scenario(name="Background", line=number)
            feature.background = current
            continue
        if match := SCENARIO.match(line):
            current = Scenario(name=match.group("name"), line=number)
            feature.scenarios.append(current)
            continue
        if tag_match := TAG.match(line):
            feature.tags.update(tag.lstrip("@") for tag in tag_match.group(1).split())
            continue
        if line.startswith(("Examples:", "|", "@", "Rule:")):
            continue
        if (match := STEP.match(line)) and current is not None:
            current.steps.append((number, match.group("keyword"), match.group("text")))
    return feature


def discover_features(directory: Path) -> list[Path]:
    """Return every ``.feature`` file under ``directory`` in a stable order."""
    return sorted(directory.rglob("*.feature")) if directory.is_dir() else []


def discover_step_definitions(directory: Path) -> list[StepDefinition]:
    """Return every ``pytest-bdd`` step definition under ``directory``."""
    definitions: list[StepDefinition] = []
    for path in sorted(directory.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        for match in STEP_DEFINITION.finditer(text):
            definitions.append(
                StepDefinition(
                    path=str(path),
                    line=text.count("\n", 0, match.start()) + 1,
                    keyword=match.group(0).split("(", 1)[0].lstrip("@"),
                    text=match.group("text"),
                )
            )
    return definitions


def _check_order(scenario: Scenario, path: str) -> Iterable[Finding]:
    phase = -1
    keyword_seen = "Given"
    for number, keyword, _ in scenario.steps:
        if keyword in PHASES:
            keyword_seen = keyword
            if PHASES[keyword] < phase:
                yield Finding(
                    path,
                    number,
                    "PSF-FEAT-005",
                    f"'{keyword}' step after a later phase in scenario '{scenario.name}'",
                )
            phase = max(phase, PHASES[keyword])
        elif keyword in {"And", "But", "*"} and phase < 0:
            yield Finding(
                path,
                number,
                "PSF-FEAT-005",
                f"'{keyword}' step without a preceding Given/When/Then "
                f"(after {keyword_seen}) in scenario '{scenario.name}'",
            )


def _as_dirs(value: Path | Sequence[Path] | None, default: tuple[Path, ...]) -> tuple[Path, ...]:
    """Normalise a one-or-many directory argument, falling back to the default."""
    if value is None:
        return default
    return (value,) if isinstance(value, Path) else tuple(value)


def lint_features(
    features_dirs: Path | Sequence[Path] | None = None,
    steps_dirs: Path | Sequence[Path] | None = None,
    *,
    allowed_tags: frozenset[str] | None = None,
    root: Path = REPO_ROOT,
) -> list[Finding]:
    """Lint every feature file under ``features_dirs`` against ``steps_dirs``."""
    features_dirs = _as_dirs(features_dirs, FEATURES_DIRS)
    steps_dirs = _as_dirs(steps_dirs, STEPS_DIRS)
    definitions = [
        definition
        for directory in steps_dirs
        for definition in discover_step_definitions(directory)
    ]
    findings: list[Finding] = []
    used: set[int] = set()
    paths = [path for directory in features_dirs for path in discover_features(directory)]

    for path in paths:
        relative = str(path.relative_to(root)) if path.is_relative_to(root) else str(path)
        feature = parse_feature(path)
        if not feature.name:
            findings.append(Finding(relative, 1, "PSF-FEAT-001", "no Feature: statement"))
            continue
        if not feature.scenarios:
            findings.append(Finding(relative, feature.line, "PSF-FEAT-002", "no scenarios"))
        if allowed_tags is not None:
            for tag in sorted(feature.tags - allowed_tags):
                findings.append(
                    Finding(relative, feature.line, "PSF-FEAT-008", f"unknown tag {tag}")
                )

        background_steps = feature.background.steps if feature.background else []
        if feature.background is not None:
            findings.extend(_check_order(feature.background, relative))
        for number, _, text in background_steps:
            matching = [
                index for index, definition in enumerate(definitions) if definition.matches(text)
            ]
            if not matching:
                findings.append(
                    Finding(relative, number, "PSF-FEAT-006", f"undefined step: {text}")
                )
            used.update(matching)

        names: set[str] = set()
        for scenario in feature.scenarios:
            if scenario.name in names:
                findings.append(
                    Finding(
                        relative,
                        scenario.line,
                        "PSF-FEAT-004",
                        f"duplicate scenario name '{scenario.name}'",
                    )
                )
            names.add(scenario.name)
            if not scenario.steps:
                findings.append(
                    Finding(
                        relative,
                        scenario.line,
                        "PSF-FEAT-003",
                        f"scenario '{scenario.name}' has no steps",
                    )
                )
            findings.extend(_check_order(scenario, relative))
            for number, _, text in scenario.steps:
                matching = [
                    index
                    for index, definition in enumerate(definitions)
                    if definition.matches(text)
                ]
                if not matching:
                    findings.append(
                        Finding(relative, number, "PSF-FEAT-006", f"undefined step: {text}")
                    )
                used.update(matching)

    for index, definition in enumerate(definitions):
        if index not in used:
            findings.append(
                Finding(
                    definition.path,
                    definition.line,
                    "PSF-FEAT-007",
                    f"unused step definition: {definition.text}",
                )
            )
    return sorted(set(findings))


def load_config(path: Path = REPO_ROOT / "gherlint.toml") -> dict[str, object]:
    """Read ``gherlint.toml`` if present (tolerates a missing file)."""
    if not path.is_file():
        return {}
    return tomllib.loads(path.read_text(encoding="utf-8"))


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="python -m automation.gherkin",
        description="Lint Gherkin features and verify step definitions.",
    )
    parser.add_argument(
        "--features",
        type=Path,
        nargs="+",
        default=list(FEATURES_DIRS),
        help="feature directories (default: every tree with scenarios)",
    )
    parser.add_argument(
        "--steps",
        type=Path,
        nargs="+",
        default=list(STEPS_DIRS),
        help="step-definition directories (default: every tree with steps)",
    )
    parser.add_argument("--config", type=Path, default=REPO_ROOT / "gherlint.toml")
    parser.add_argument("--json", action="store_true", help="emit JSON findings")
    args = parser.parse_args(argv)

    config = load_config(args.config)
    tags_section = config.get("tags")
    allowed = (
        frozenset(str(tag) for tag in tags_section["allowed"])
        if isinstance(tags_section, dict) and isinstance(tags_section.get("allowed"), list)
        else None
    )
    reporting = config.get("reporting")
    disabled = (
        {str(code) for code in reporting.get("disable", [])}
        if isinstance(reporting, dict) and isinstance(reporting.get("disable"), list)
        else set()
    )

    findings = [
        finding
        for finding in lint_features(args.features, args.steps, allowed_tags=allowed)
        if finding.code not in disabled
    ]
    if args.json:
        print(json.dumps([finding.to_dict() for finding in findings], indent=2))
    else:
        for finding in findings:
            print(finding.format())
        files = sum(len(discover_features(directory)) for directory in args.features)
        status = "ok" if not findings else f"{len(findings)} finding(s)"
        print(f"features: {files} file(s), {status}")
    if findings and not args.json:
        print(
            f"codes: {', '.join(sorted({finding.code for finding in findings}))}",
            file=sys.stderr,
        )
    return 1 if findings else 0


if __name__ == "__main__":  # pragma: no cover - module entry point
    raise SystemExit(main())
