"""Steps for ``automation/features/session_restore.feature``."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from pytest_bdd import given, then, when

from automation.restore import generate

#: The three collaborators `generate.restore` accepts, named so the fakes below
#: can be typed as precisely as the real function expects them.
Finder = Callable[[str], str | None]
Installer = Callable[..., str | None]
GitRunner = Callable[..., str]


class Recorder:
    """Records subprocess calls and fakes the resulting filesystem state."""

    def __init__(self, root: Path, *, fail_install: bool = False) -> None:
        self.root = root
        self.fail_install = fail_install
        self.calls: list[tuple[str, ...]] = []

    def run(self, command: list[str], *, cwd: Path, env: object = None) -> int:
        self.calls.append(tuple(command))
        if "install" in command:
            if self.fail_install:
                return 1
            environment = self.root / ".pixi" / "envs" / "default"
            environment.mkdir(parents=True, exist_ok=True)
        if "install-hooks" in command:
            hook = self.root / ".git" / "hooks" / "pre-commit"
            hook.parent.mkdir(parents=True, exist_ok=True)
            hook.write_text(f"#!/bin/sh\n# {generate.HOOK_MARKER}\n", encoding="utf-8")
        return 0


def _git(git_dir: str) -> GitRunner:
    def runner(command: list[str], *, cwd: Path) -> str:
        return git_dir if command[:3] == ["git", "rev-parse", "--git-dir"] else ""

    return runner


def _on_path(name: str) -> str | None:
    return f"/usr/local/bin/{name}" if name == "pixi" else None


def _restore(context: dict[str, Any], *, finder: Finder, fail_install: bool = False) -> None:
    root = Path(str(context["root"]))
    recorder = Recorder(root, fail_install=fail_install)
    installer: Installer = context.get("installer") or _fake_installer(root)
    try:
        context["state"] = generate.restore(
            root,
            tooling=generate.Tooling(
                runner=recorder.run,
                fetcher=lambda url: b"#!/bin/sh\n",
                finder=finder,
                git=_git(str(context.get("git_dir", ""))),
                installer=installer,
            ),
        )
    except RuntimeError as error:
        context["error"] = str(error)
    context["calls"] = recorder.calls


def _fake_installer(root: Path) -> Installer:
    """An installer that creates the environment and reports a binary."""

    def install(**kwargs: object) -> str:
        (root / ".pixi" / "envs" / "default").mkdir(parents=True, exist_ok=True)
        return "/home/user/.pixi/bin/pixi"

    return install


@given("a repository without Pixi")
def without_pixi(tmp_path: Path, context: dict[str, Any]) -> None:
    context["root"] = tmp_path / "repo"
    context["finder"] = lambda name: None


@given("a repository with Pixi on the PATH")
def with_pixi(tmp_path: Path, context: dict[str, Any]) -> None:
    context["root"] = tmp_path / "repo"
    context["finder"] = _on_path


@given("a repository with Pixi on the PATH inside a git checkout")
def with_pixi_and_git(tmp_path: Path, context: dict[str, Any]) -> None:
    context["root"] = tmp_path / "repo"
    context["finder"] = _on_path
    context["git_dir"] = ".git"


@given("a repository with Pixi on the PATH and no git checkout")
def with_pixi_without_git(tmp_path: Path, context: dict[str, Any]) -> None:
    context["root"] = tmp_path / "repo"
    context["finder"] = _on_path
    context["git_dir"] = ""


@given("a repository whose environment cannot be solved")
def unsolvable(tmp_path: Path, context: dict[str, Any]) -> None:
    context["root"] = tmp_path / "repo"
    context["finder"] = _on_path
    context["unsolvable"] = True


@when("I restore the session")
def restore(context: dict[str, Any]) -> None:
    if context.get("unsolvable"):
        _restore(context, finder=context["finder"], fail_install=True)
        return
    _restore(context, finder=context["finder"])


@then("Pixi is installed from the official installer")
def installed(context: dict[str, Any]) -> None:
    state = context["state"]
    assert state.pixi is not None


@then("the installer is not run")
def installer_not_run(context: dict[str, Any]) -> None:
    calls = context["calls"]
    assert ("/usr/local/bin/pixi", "install", "--locked") in calls
    assert not any(call[0] == "sh" for call in calls)


@then("the environment is solved with the lock file")
def solved(context: dict[str, Any]) -> None:
    assert any("--locked" in call and "install" in call for call in context["calls"])


@then("the Lefthook hooks are installed")
def hooks_installed(context: dict[str, Any]) -> None:
    state = context["state"]
    assert state.hooks is True
    assert any("install-hooks" in call for call in context["calls"])


@then("the hooks are reported as skipped")
def hooks_skipped(context: dict[str, Any]) -> None:
    state = context["state"]
    assert state.git is False
    assert state.complete is True
    assert not any("install-hooks" in call for call in context["calls"])


@then("the session restore reports a failure")
def reports_failure(context: dict[str, Any]) -> None:
    assert "error" in context
    assert "pixi install" in str(context["error"])
