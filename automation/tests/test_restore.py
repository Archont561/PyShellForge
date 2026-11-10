"""Tests for ``automation.restore``."""

from __future__ import annotations

import json
import os
from collections.abc import Callable, Sequence
from pathlib import Path

import pytest

from automation.restore import generate


class Recorder:
    """A stand-in for ``subprocess_runner`` plus a git double."""

    def __init__(self) -> None:
        self.calls: list[tuple[tuple[str, ...], Path]] = []

    def run(self, command: tuple[str, ...] | list[str], *, cwd: Path, env: object = None) -> int:
        self.calls.append((tuple(command), Path(cwd)))
        return 0

    def commands(self) -> list[tuple[str, ...]]:
        return [command for command, _ in self.calls]


def no_pixi(_name: str) -> None:
    return None


def found_pixi(name: str) -> str | None:
    return f"/usr/local/bin/{name}" if name == "pixi" else None


def fake_git(git_dir: str = "") -> Callable[..., str]:
    """A git runner that reports ``git_dir`` for ``rev-parse --git-dir``."""

    def runner(command: Sequence[str], *, cwd: Path) -> str:
        return git_dir if list(command[:3]) == ["git", "rev-parse", "--git-dir"] else ""

    return runner


def make_environment(root: Path) -> Path:
    """Pretend ``pixi install`` has run."""
    env = root / ".pixi" / "envs" / "default"
    env.mkdir(parents=True)
    return env


def make_hook(root: Path, marker: str = generate.HOOK_MARKER) -> Path:
    """Pretend Lefthook installed a hook and git knows about it."""
    hook = root / ".git" / "hooks" / "pre-commit"
    hook.parent.mkdir(parents=True)
    hook.write_text(f"#!/bin/sh\n# {marker} hook\n", encoding="utf-8")
    return hook


# -- detection -----------------------------------------------------------------
def test_which_pixi_prefers_path() -> None:
    assert generate.which_pixi(finder=found_pixi) == "/usr/local/bin/pixi"


def test_which_pixi_falls_back_to_pixi_home(tmp_path: Path) -> None:
    binary = tmp_path / "bin" / "pixi"
    binary.parent.mkdir(parents=True)
    binary.write_text("", encoding="utf-8")
    assert generate.which_pixi(finder=no_pixi, pixi_home=tmp_path) == str(binary)


def test_which_pixi_returns_none_when_absent(tmp_path: Path) -> None:
    assert generate.which_pixi(finder=no_pixi, pixi_home=tmp_path) is None


def test_which_pixi_repairs_a_binary_that_lost_its_executable_bit(tmp_path: Path) -> None:
    binary = tmp_path / "bin" / "pixi"
    binary.parent.mkdir(parents=True)
    binary.write_text("#!/bin/sh\n", encoding="utf-8")
    binary.chmod(0o644)

    assert generate.which_pixi(finder=no_pixi, pixi_home=tmp_path) == str(binary)
    assert os.access(binary, os.X_OK), "the executable bit must be restored"


def test_make_executable_is_a_noop_on_an_executable(tmp_path: Path) -> None:
    binary = tmp_path / "pixi"
    binary.write_text("", encoding="utf-8")
    binary.chmod(0o755)
    assert generate.make_executable(binary) is False


def test_install_environment_reports_an_unrunnable_binary(tmp_path: Path) -> None:
    def runner(command: list[str], *, cwd: Path, env: object = None) -> int:
        raise PermissionError(13, "Permission denied", command[0])

    with pytest.raises(RuntimeError, match="could not run"):
        generate.install_environment(tmp_path, "/home/user/.pixi/bin/pixi", runner=runner)


def test_install_hooks_reports_an_unrunnable_binary(tmp_path: Path) -> None:
    def runner(command: list[str], *, cwd: Path, env: object = None) -> int:
        raise PermissionError(13, "Permission denied", command[0])

    with pytest.raises(RuntimeError, match="could not run"):
        generate.install_hooks(tmp_path, "/home/user/.pixi/bin/pixi", runner=runner)


def test_environment_ready_follows_the_env_directory(tmp_path: Path) -> None:
    assert generate.environment_ready(tmp_path) is False
    make_environment(tmp_path)
    assert generate.environment_ready(tmp_path) is True


def test_is_git_repository(tmp_path: Path) -> None:
    assert generate.is_git_repository(tmp_path, runner=fake_git("")) is False
    assert generate.is_git_repository(tmp_path, runner=fake_git(".git")) is True


def test_hooks_installed_reads_the_pre_commit_hook(tmp_path: Path) -> None:
    runner = fake_git(".git")
    assert generate.hooks_installed(tmp_path, runner=runner) is False
    make_hook(tmp_path)
    assert generate.hooks_installed(tmp_path, runner=runner) is True


def test_hooks_installed_ignores_a_foreign_hook(tmp_path: Path) -> None:
    make_hook(tmp_path, marker="husky")
    assert generate.hooks_installed(tmp_path, runner=fake_git(".git")) is False


def test_hooks_installed_without_git(tmp_path: Path) -> None:
    make_hook(tmp_path)
    assert generate.hooks_installed(tmp_path, runner=fake_git("")) is False


def test_state_completeness(tmp_path: Path) -> None:
    ready = generate.State(pixi="/pixi", environment=True, git=True, hooks=True)
    assert ready.complete is True
    no_git = generate.State(pixi="/pixi", environment=True, git=False, hooks=False)
    assert no_git.complete is True, "hooks are not expected outside a git checkout"
    assert generate.State(pixi=None, environment=True, git=False, hooks=False).complete is False
    assert generate.State(pixi="/pixi", environment=False, git=False, hooks=False).complete is False
    assert generate.State(pixi="/pixi", environment=True, git=True, hooks=False).complete is False


def test_state_serialises_with_completeness() -> None:
    payload = generate.State(pixi="/pixi", environment=True, git=False, hooks=False).to_dict()
    assert payload["complete"] is True
    json.dumps(payload)


# -- installation --------------------------------------------------------------
def test_install_pixi_runs_the_downloaded_installer(tmp_path: Path) -> None:
    binary = tmp_path / "bin" / "pixi"
    recorder = Recorder()
    seen: dict[str, object] = {}

    def fetcher(url: str) -> bytes:
        seen["url"] = url
        return b"#!/bin/sh\nexit 0\n"

    def runner(command: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> int:
        seen["env"] = env
        binary.parent.mkdir(parents=True, exist_ok=True)
        binary.write_text("", encoding="utf-8")
        return recorder.run(command, cwd=cwd)

    installed = generate.install_pixi(fetcher=fetcher, runner=runner, pixi_home=tmp_path)

    assert seen["url"] == generate.INSTALLER_URL
    assert installed == str(binary)
    assert recorder.commands()[0][0] == "sh"
    env = seen["env"]
    assert isinstance(env, dict)
    assert env["PIXI_HOME"] == str(tmp_path)
    assert env["PIXI_VERSION"] == generate.PIXI_VERSION
    assert env["PIXI_NO_PATH_UPDATE"] == "1"


def test_install_pixi_raises_on_installer_failure(tmp_path: Path) -> None:
    def runner(command: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> int:
        return 2

    with pytest.raises(RuntimeError, match="exited with status 2"):
        generate.install_pixi(fetcher=lambda url: b"#!/bin/sh\n", runner=runner, pixi_home=tmp_path)


def test_install_pixi_raises_when_no_binary_appears(tmp_path: Path) -> None:
    def runner(command: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> int:
        return 0

    with pytest.raises(RuntimeError, match="did not create"):
        generate.install_pixi(fetcher=lambda url: b"#!/bin/sh\n", runner=runner, pixi_home=tmp_path)


def test_install_pixi_rejects_an_empty_installer(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="was empty"):
        generate.install_pixi(fetcher=lambda url: b"", runner=Recorder().run, pixi_home=tmp_path)


def test_binary_path_uses_the_platform_name(tmp_path: Path) -> None:
    assert generate.binary_path(tmp_path).parent.name == "bin"
    assert generate.binary_path(tmp_path).name in {"pixi", "pixi.exe"}


def test_install_pixi_raises_when_the_installer_leaves_no_executable(tmp_path: Path) -> None:
    binary = tmp_path / "bin" / "pixi"
    binary.parent.mkdir(parents=True)
    binary.write_text("", encoding="utf-8")
    binary.chmod(0o644)

    installed = generate.install_pixi(
        fetcher=lambda url: b"#!/bin/sh\n",
        runner=lambda command, *, cwd, env=None: 0,
        pixi_home=tmp_path,
    )
    assert installed == str(binary)
    assert os.access(binary, os.X_OK)


def test_pixi_env_puts_the_binary_first_on_path() -> None:
    env = generate.pixi_env("/opt/pixi/bin/pixi")
    assert env["PATH"].split(":")[0] == "/opt/pixi/bin"


# -- orchestration -------------------------------------------------------------
def test_restore_installs_pixi_environment_and_hooks(tmp_path: Path) -> None:
    recorder = Recorder()
    make_environment(tmp_path)
    make_hook(tmp_path)

    state = generate.restore(
        tmp_path,
        runner=recorder.run,
        fetcher=lambda url: b"#!/bin/sh\n",
        finder=found_pixi,
        git_runner_=fake_git(".git"),
        hooks=True,
    )

    assert recorder.commands() == [
        ("/usr/local/bin/pixi", "install", "--locked"),
        ("/usr/local/bin/pixi", "run", "--locked", "install-hooks"),
    ]
    assert state.complete is True


def test_restore_relocks_first(tmp_path: Path) -> None:
    recorder = Recorder()
    make_environment(tmp_path)

    generate.restore(
        tmp_path,
        runner=recorder.run,
        fetcher=lambda url: b"",
        finder=found_pixi,
        git_runner_=fake_git(""),
        relock=True,
        hooks=False,
    )

    assert recorder.commands()[0] == ("/usr/local/bin/pixi", "lock")
    assert recorder.commands()[1] == ("/usr/local/bin/pixi", "install", "--locked")


def test_restore_skips_hooks_without_git(tmp_path: Path) -> None:
    recorder = Recorder()
    make_environment(tmp_path)

    generate.restore(
        tmp_path,
        runner=recorder.run,
        fetcher=lambda url: b"",
        finder=found_pixi,
        git_runner_=fake_git(""),
    )

    assert recorder.commands() == [("/usr/local/bin/pixi", "install", "--locked")]


def test_restore_skips_hooks_when_asked(tmp_path: Path) -> None:
    recorder = Recorder()
    make_environment(tmp_path)

    generate.restore(
        tmp_path,
        runner=recorder.run,
        fetcher=lambda url: b"",
        finder=found_pixi,
        git_runner_=fake_git(".git"),
        hooks=False,
    )

    assert ("/usr/local/bin/pixi", "run", "--locked", "install-hooks") not in recorder.commands()


def test_restore_raises_when_the_environment_cannot_be_solved(tmp_path: Path) -> None:
    def runner(command: list[str], *, cwd: Path, env: object = None) -> int:
        return 1

    with pytest.raises(RuntimeError, match="pixi install"):
        generate.restore(
            tmp_path,
            runner=runner,
            fetcher=lambda url: b"",
            finder=found_pixi,
            git_runner_=fake_git(""),
        )


def test_restore_raises_when_hooks_fail(tmp_path: Path) -> None:
    calls: list[tuple[str, ...]] = []

    def runner(command: list[str], *, cwd: Path, env: object = None) -> int:
        calls.append(tuple(command))
        return 0 if "install" in command else 3

    make_environment(tmp_path)
    with pytest.raises(RuntimeError, match="install-hooks"):
        generate.restore(
            tmp_path,
            runner=runner,
            fetcher=lambda url: b"",
            finder=found_pixi,
            git_runner_=fake_git(".git"),
        )
    assert ("/usr/local/bin/pixi", "run", "--locked", "install-hooks") in calls


# -- CLI -----------------------------------------------------------------------
def test_main_check_reports_missing_state(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch_finder = pytest.MonkeyPatch()
    monkeypatch_finder.setattr(generate, "which_pixi", lambda **kwargs: None)
    try:
        assert generate.main(["--root", str(tmp_path), "--check"]) == 1
    finally:
        monkeypatch_finder.undo()
    output = capsys.readouterr().out
    assert "pixi missing" in output
    assert "repository is not ready" in output


def test_main_check_json(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert generate.main(["--root", str(tmp_path), "--check", "--json"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["complete"] is False


def test_main_check_passes_when_ready(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    make_environment(tmp_path)
    monkeypatch.setattr(generate, "which_pixi", lambda **kwargs: "/usr/local/bin/pixi")
    assert generate.main(["--root", str(tmp_path), "--check"]) == 0


def test_main_restore_reports_a_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def boom(root: Path, **kwargs: object) -> generate.State:
        raise RuntimeError("the Pixi installer exited with status 1")

    monkeypatch.setattr(generate, "restore", boom)
    assert generate.main(["--root", str(tmp_path)]) == 1
    assert "installer exited" in capsys.readouterr().out


def test_main_restore_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        generate,
        "restore",
        lambda root, **kwargs: generate.State(
            pixi="/pixi", environment=True, git=False, hooks=False
        ),
    )
    assert generate.main(["--root", str(tmp_path)]) == 0
    output = capsys.readouterr().out
    assert "hooks skipped" in output
    assert "repository is ready" in output


def test_main_passes_the_version_through(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, object] = {}

    def fake_restore(root: Path, **kwargs: object) -> generate.State:
        seen.update(kwargs)
        return generate.State(pixi="/pixi", environment=True, git=False, hooks=False)

    monkeypatch.setattr(generate, "restore", fake_restore)
    generate.main(["--root", str(tmp_path), "--version", "9.9.9", "--relock", "--skip-hooks"])
    assert seen["version"] == "9.9.9"
    assert seen["relock"] is True
    assert seen["hooks"] is False
