"""Steps for ``automation/features/automation_cli.feature``.

The subject is the registry itself (``dodo.py``), not one of the modules: these
scenarios pin the contract that makes the CLI discoverable and safe.
"""

from __future__ import annotations

import importlib
from collections.abc import Callable
from typing import Any

import pytest
from pytest_bdd import given, then, when


def registry() -> Any:
    """Import the task registry fresh; importing it must stay side-effect free."""
    return importlib.import_module("dodo")


def tasks(module: Any) -> dict[str, dict[str, Any]]:
    """Return ``{basename: task spec}`` for every ``task_*`` creator."""
    found: dict[str, dict[str, Any]] = {}
    for name in dir(module):
        if not name.startswith("task_"):
            continue
        spec = getattr(module, name)()
        found[str(spec["basename"])] = spec
    return found


@given("the task registry", target_fixture="registry_module")
def registry_module() -> Any:
    return registry()


@when("I read every task")
def read_every_task(registry_module: Any, context: dict[str, Any]) -> None:
    context["tasks"] = tasks(registry_module)


@given("a module whose entry point returns zero")
def succeeding_module(context: dict[str, Any]) -> None:
    context["main"] = lambda argv=None: 0


@given("a module whose entry point returns a failure status")
def failing_module(context: dict[str, Any]) -> None:
    context["main"] = lambda argv=None: 3


@given("a module whose entry point raises when called")
def exploding_module(monkeypatch: pytest.MonkeyPatch) -> None:
    def explode(*_: object) -> int:  # pragma: no cover - must never be called
        raise AssertionError("the registry ran automation at import time")

    monkeypatch.setattr("automation.docs.main", explode)


@when("the registry adapter runs it")
def run_through_adapter(context: dict[str, Any]) -> None:
    module = registry()
    action: Callable[[], None] = module._run(context["main"], None)
    context["error"] = None
    try:
        action()
    except RuntimeError as error:
        context["error"] = str(error)


@when("the registry is imported")
def import_registry(context: dict[str, Any]) -> None:
    context["error"] = None
    try:
        importlib.reload(registry())
    except AssertionError as error:  # pragma: no cover - only fails on a regression
        context["error"] = str(error)


@then("every task name is kebab-case")
def names_are_kebab_case(context: dict[str, Any]) -> None:
    for name in context["tasks"]:
        assert name == name.lower(), name
        assert "_" not in name, f"{name!r} should read as a command, not an identifier"


@then("the check task depends on every gate in the graph")
def check_depends_on_every_gate(registry_module: Any, context: dict[str, Any]) -> None:
    known = context["tasks"]
    gates = tuple(registry_module.GATES)
    assert "check" in known, "the aggregate gate is not registered"
    assert tuple(known["check"]["task_dep"]) == gates
    missing = [gate for gate in gates if gate not in known]
    assert missing == [], f"gates without a task: {missing}"


@then("the check task declares no actions of its own")
def check_has_no_actions(context: dict[str, Any]) -> None:
    assert context["tasks"]["check"]["actions"] == []


@then("the task succeeds")
def task_succeeds(context: dict[str, Any]) -> None:
    assert context["error"] is None


@then("the task fails with a message naming the status")
def task_fails(context: dict[str, Any]) -> None:
    error = context["error"]
    assert error is not None
    assert "exit status 3" in str(error)


@then("the import completes without running anything")
def import_is_quiet(context: dict[str, Any]) -> None:
    assert context["error"] is None


@then("the release-build task offers a ref and a tag-check switch")
def release_params(context: dict[str, Any]) -> None:
    spec = context["tasks"]["release-build"]
    names = {param["name"] for param in spec["params"]}
    assert {"ref", "skip_tag_check"} <= names


@then("the detect-changes task offers a base, a head and an event")
def detect_params(context: dict[str, Any]) -> None:
    spec = context["tasks"]["detect-changes"]
    names = {param["name"] for param in spec["params"]}
    assert names == {"base", "head", "event"}
