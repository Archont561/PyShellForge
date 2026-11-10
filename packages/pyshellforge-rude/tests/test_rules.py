"""The scope casing rules, exercised through Rude's public linter API."""

from __future__ import annotations

from importlib.metadata import entry_points

import pytest
from rude import Linter, Rule

from pyshellforge_rude import RULES
from pyshellforge_rude.rules import LocalsAreLowerCase, ModuleGlobalsAreUpperCase

#: Every fixture file has to look like a definition, or the rules skip it.
HEADER = "from pyshellforge import Int, Path, Str, sh\n\n"


def found(source: str, rule: type[Rule] | None = None) -> list[tuple[str, int]]:
    """Lint ``source`` and return code/line pairs."""
    linter = Linter()
    for rule_class in RULES if rule is None else [rule]:
        linter.register(rule_class())
    return [(item.code, item.location.line) for item in linter.check_source(source)]


def test_the_plugin_exports_both_rules() -> None:
    assert [rule.code for rule in RULES] == ["PSF201", "PSF202"]


def test_the_plugin_is_discoverable_through_the_entry_point() -> None:
    # The manifest is the install step: without this entry point Rude never
    # imports the module, however correct the rules are.
    names = {entry.name for entry in entry_points(group="rude.plugins")}
    assert "pyshellforge_rude" in names


@pytest.mark.parametrize(
    "declaration",
    [
        'NAME: Str = "release"',
        "_TIMEOUT: Int = 30",
        "MAX2: Int = 2",
        'ROOT: Path = "/srv/app"',
    ],
)
def test_module_globals_in_upper_case_are_accepted(declaration: str) -> None:
    assert found(HEADER + declaration + "\n") == []


@pytest.mark.parametrize(
    ("declaration", "line"),
    [
        ('target_dir: Path = "/srv/app"', 3),
        ("MaxRetries: Int = 3", 3),
        ("i = 0", 3),
    ],
)
def test_module_globals_in_other_cases_are_reported(declaration: str, line: int) -> None:
    assert found(HEADER + declaration + "\n") == [("PSF201", line)]


def test_chained_assignment_reports_every_name() -> None:
    source = HEADER + "first = second = 1\n"
    assert sorted(found(source)) == [("PSF201", 3), ("PSF201", 3)]


@pytest.mark.parametrize(
    "declaration",
    [
        "import os",
        "from pathlib import Path",
        "from __future__ import annotations",
    ],
)
def test_imports_and_type_aliases_are_not_shell_variables(declaration: str) -> None:
    assert found(HEADER + declaration + "\n") == []


def test_class_attributes_are_not_script_globals() -> None:
    source = HEADER + "class Settings:\n    timeout: Int = 5\n"
    assert found(source) == []


def test_module_level_loop_target_is_left_to_the_compiler() -> None:
    source = HEADER + "for i in range(3):\n    pass\n"
    assert found(source) == []


def test_function_locals_in_lower_case_are_accepted() -> None:
    source = HEADER + "@sh\ndef build(jobs: Int = 4) -> None:\n    count = 0\n    out(count)\n"
    assert found(source) == []


def test_function_locals_in_upper_case_are_reported() -> None:
    source = HEADER + "@sh\ndef build() -> None:\n    TMP = 1\n"
    assert found(source) == [("PSF202", 5)]


def test_upper_case_parameter_is_reported() -> None:
    source = HEADER + "@sh\ndef build(OUT_DIR: Path) -> None:\n    out(OUT_DIR)\n"
    assert found(source) == [("PSF202", 4)]


@pytest.mark.parametrize("name", ["self", "cls", "_"])
def test_exempt_names_are_not_reported(name: str) -> None:
    source = HEADER + f"@sh\ndef build({name}) -> None:\n    pass\n"
    assert found(source) == []


def test_global_declaration_keeps_the_module_convention() -> None:
    source = (
        HEADER
        + "MAX_JOBS: Int = 4\n\n@sh\ndef build() -> None:\n    global MAX_JOBS\n    MAX_JOBS = 2\n"
    )
    assert found(source) == []


def test_files_without_the_markers_are_ignored() -> None:
    source = "import os\n\ntarget_dir = 1\n"
    assert found(source) == []


def test_the_rules_are_independent() -> None:
    source = HEADER + "target_dir = 1\n\n@sh\ndef build() -> None:\n    TMP = 1\n"
    assert found(source, ModuleGlobalsAreUpperCase) == [("PSF201", 3)]
    assert found(source, LocalsAreLowerCase) == [("PSF202", 7)]
