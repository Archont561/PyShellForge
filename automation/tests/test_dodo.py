"""Tests for the task registry in ``dodo.py``.

The registry is the CLI's contract: doit discovers tasks by importing it, so
these tests pin the naming, the gate graph and the two adapters (a module's exit
status, and the release task's parameters) without running doit.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import pytest

import dodo


def tasks() -> dict[str, dict[str, Any]]:
    """Return ``{basename: spec}`` for every ``task_*`` creator in the registry."""
    found: dict[str, dict[str, Any]] = {}
    for name in dir(dodo):
        if name.startswith("task_"):
            spec = getattr(dodo, name)()
            found[spec["basename"]] = spec
    return found


# -- naming ------------------------------------------------------------------
def test_every_task_is_named_like_a_command() -> None:
    names = tasks()
    assert names, "the registry is empty"
    for name in names:
        assert name == name.lower()
        assert "_" not in name, f"{name!r} should read as a command, not an identifier"


def test_every_task_carries_its_docstring() -> None:
    for name, spec in tasks().items():
        assert spec["actions"] == [] or spec["actions"], name
        function = getattr(dodo, f"task_{name.replace('-', '_')}")
        assert function.__doc__, f"{name} has no docstring for `doit list`"


def test_the_default_is_to_list_rather_than_to_run() -> None:
    assert dodo.DOIT_CONFIG["default_tasks"] == ["list"]


# -- the gate ----------------------------------------------------------------
def test_the_aggregate_task_only_wires_dependencies() -> None:
    assert tasks()["check"] == {"basename": "check", "actions": [], "task_dep": list(dodo.GATES)}


def test_every_gate_has_a_task() -> None:
    known = tasks()
    missing = [gate for gate in dodo.GATES if gate not in known]
    assert missing == []


def test_no_task_declares_a_cache() -> None:
    """Side effects must never be skipped because a file looked fresh."""
    for name, spec in tasks().items():
        assert "file_dep" not in spec, name
        assert "targets" not in spec, name


# -- the module adapter ------------------------------------------------------
def test_a_module_that_succeeds_is_a_passing_action() -> None:
    assert dodo._run(lambda argv: 0)() is None


def test_a_module_that_fails_raises_with_its_status() -> None:
    with pytest.raises(RuntimeError, match="exit status 2"):
        dodo._run(lambda argv: 2)()


def test_the_adapter_passes_its_arguments_through() -> None:
    seen: list[list[str]] = []

    def main(argv: Sequence[str] | None) -> int:
        seen.append(list(argv or []))
        return 0

    dodo._run(main, ["--check"])()
    assert seen == [["--check"]]


def test_the_adapter_defaults_to_no_arguments() -> None:
    seen: list[list[str]] = []

    def main(argv: Sequence[str] | None) -> int:
        seen.append(list(argv or []))
        return 0

    dodo._run(main)()
    assert seen == [[]]


# -- the release parameters --------------------------------------------------
@pytest.fixture
def release_argv(monkeypatch: pytest.MonkeyPatch) -> list[list[str]]:
    """Capture the argv the release task builds instead of running a build."""
    captured: list[list[str]] = []

    def fake_main(argv: list[str] | None = None) -> int:
        captured.append(list(argv or []))
        return 0

    monkeypatch.setattr(dodo.release, "main", fake_main)
    return captured


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        ({}, []),
        ({"ref": "v0.1.0"}, ["--ref", "v0.1.0"]),
        ({"skip_tag_check": True}, ["--skip-tag-check"]),
        ({"ref": "v0.1.0", "skip_tag_check": True}, ["--ref", "v0.1.0", "--skip-tag-check"]),
    ],
)
def test_the_release_task_translates_its_parameters(
    release_argv: list[list[str]], kwargs: dict[str, object], expected: list[str]
) -> None:
    dodo._release_build(**kwargs)  # type: ignore[arg-type]
    assert release_argv == [expected]


def test_a_failing_release_build_fails_the_task(release_argv: list[list[str]]) -> None:
    def failing(argv: list[str] | None = None) -> int:
        return 1

    dodo.release.main = failing  # type: ignore[assignment]
    with pytest.raises(RuntimeError, match="exit status 1"):
        dodo._release_build()
