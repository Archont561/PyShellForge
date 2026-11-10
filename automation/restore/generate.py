"""Restore the developer environment at the start of a session.

A fresh checkout, a new machine or a short-lived sandbox has the source but
neither Pixi nor a solved environment. This script is the one command that gets
from there to a working repository:

1. locate ``pixi`` on ``PATH`` or in ``~/.pixi/bin``;
2. install it from the official installer when it is missing;
3. create the environment with ``pixi install --locked``;
4. install the Lefthook git hooks with ``pixi run install-hooks``.

Every step is skippable and reported, so the script is safe to re-run and safe to
run in a container that has no git checkout: it says what it skipped and why
instead of pretending the work happened.

Usage::

    python -m automation.restore            # ensure pixi, solve the env, install hooks
    python -m automation.restore --check    # report state only, exit 1 when incomplete
    python -m automation.restore --relock   # run `pixi lock` before installing
    python -m automation.restore --skip-hooks

The Pixi version is pinned here and can be overridden with ``--version`` or
``PSF_PIXI_VERSION``; the version actually installed is printed.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

#: Repository root, derived from this file (``automation/restore/generate.py``).
REPO_ROOT = Path(__file__).resolve().parents[2]

#: Pixi release the installer is asked for.
PIXI_VERSION = "0.84.1"

#: Official installer; downloaded, then executed with ``sh`` instead of piped.
INSTALLER_URL = "https://pixi.sh/install.sh"

#: Where the installer puts ``bin/pixi`` by default.
PIXI_HOME = Path.home() / ".pixi"

#: Marker lefthook writes into the hook scripts it installs.
HOOK_MARKER = "lefthook"

#: A runner executes a command and returns its exit status.
Runner = Callable[..., int]

#: A fetcher returns the bytes behind a URL.
Fetcher = Callable[[str], bytes]


@dataclass(frozen=True)
class State:
    """What the restore step found, without changing anything."""

    pixi: str | None
    environment: bool
    git: bool
    hooks: bool

    @property
    def complete(self) -> bool:
        """Whether the repository is ready for ``pixi run`` and hooks."""
        if self.pixi is None or not self.environment:
            return False
        return self.hooks or not self.git

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serialisable representation."""
        payload = asdict(self)
        payload["complete"] = self.complete
        return payload


def subprocess_runner(
    command: Sequence[str], *, cwd: Path, env: Mapping[str, str] | None = None
) -> int:
    """Run ``command`` in ``cwd`` with inherited stdio."""
    return subprocess.run(
        list(command), cwd=cwd, env=dict(env) if env else None, check=False
    ).returncode


def url_fetcher(url: str) -> bytes:
    """Download ``url`` and return its body."""
    with urllib.request.urlopen(url) as response:
        return response.read()


def make_executable(path: Path) -> bool:
    """Restore the executable bit on a binary that lost it.

    A home directory restored from a backup or a snapshot can keep the bytes and
    drop the mode, which turns ``pixi`` into a file the shell refuses to run.
    Returns whether the mode had to change.
    """
    if not path.is_file() or os.access(path, os.X_OK):
        return False
    path.chmod(path.stat().st_mode | 0o111)
    return True


def binary_path(pixi_home: Path = PIXI_HOME) -> Path:
    """Where the official installer puts the binary."""
    return pixi_home / "bin" / ("pixi.exe" if sys.platform == "win32" else "pixi")


def which_pixi(
    *, finder: Callable[[str], str | None] = shutil.which, pixi_home: Path = PIXI_HOME
) -> str | None:
    """Return the path to an executable ``pixi``, on ``PATH`` or in ``pixi_home/bin``."""
    found = finder("pixi")
    if found:
        return found
    candidate = binary_path(pixi_home)
    if not candidate.is_file():
        return None
    make_executable(candidate)
    return str(candidate) if os.access(candidate, os.X_OK) else None


def installer_env(pixi_home: Path, version: str) -> dict[str, str]:
    """Environment for the installer: keep it non-interactive and out of ``PATH`` files."""
    env = dict(os.environ)
    env.update(
        {
            "PIXI_HOME": str(pixi_home),
            "PIXI_VERSION": version,
            "PIXI_NO_PATH_UPDATE": "1",
        }
    )
    return env


def install_pixi(
    *,
    fetcher: Fetcher = url_fetcher,
    runner: Runner = subprocess_runner,
    version: str = PIXI_VERSION,
    pixi_home: Path = PIXI_HOME,
) -> str | None:
    """Install Pixi with the official installer and return the binary path.

    The script is downloaded to a temporary file and executed, rather than piped
    into a shell, so a failed download cannot execute half a script.

    Raises:
        RuntimeError: if the installer fails or leaves no binary behind.
    """
    script_bytes = fetcher(INSTALLER_URL)
    if not script_bytes:
        msg = f"the installer at {INSTALLER_URL} was empty"
        raise RuntimeError(msg)

    with tempfile.TemporaryDirectory(prefix="psf-restore-") as directory:
        script = Path(directory) / "install.sh"
        script.write_bytes(script_bytes)
        try:
            status = runner(
                ["sh", str(script)], cwd=Path(directory), env=installer_env(pixi_home, version)
            )
        except OSError as error:
            msg = f"could not run the Pixi installer: {error}"
            raise RuntimeError(msg) from error
        if status != 0:
            msg = f"the Pixi installer exited with status {status}"
            raise RuntimeError(msg)

    installed = binary_path(pixi_home)
    if not installed.is_file():
        msg = f"the Pixi installer did not create {installed}"
        raise RuntimeError(msg)
    make_executable(installed)
    if not os.access(installed, os.X_OK):
        msg = f"{installed} is not executable after the install"
        raise RuntimeError(msg)
    return str(installed)


def pixi_env(pixi: str) -> dict[str, str]:
    """Environment with the Pixi directory on ``PATH``, so nested tasks find it."""
    env = dict(os.environ)
    env["PATH"] = os.pathsep.join((str(Path(pixi).parent), env.get("PATH", "")))
    return env


def git_runner(command: Sequence[str], *, cwd: Path) -> str:
    """Run a git command and return stdout, or an empty string when it fails."""
    try:
        result = subprocess.run(list(command), cwd=cwd, check=False, capture_output=True, text=True)
    except OSError:  # pragma: no cover - git missing entirely
        return ""
    return result.stdout if result.returncode == 0 else ""


def is_git_repository(root: Path, *, runner: Callable[..., str] = git_runner) -> bool:
    """Whether ``root`` is inside a git checkout."""
    return bool(runner(["git", "rev-parse", "--git-dir"], cwd=root).strip())


def hooks_installed(root: Path, *, runner: Callable[..., str] = git_runner) -> bool:
    """Whether the Lefthook ``pre-commit`` hook is in place."""
    git_dir = runner(["git", "rev-parse", "--git-dir"], cwd=root).strip()
    if not git_dir:
        return False
    hooks_path = Path(git_dir)
    hooks_path = hooks_path if hooks_path.is_absolute() else root / hooks_path
    hook = hooks_path / "hooks" / "pre-commit"
    try:
        return HOOK_MARKER in hook.read_text(encoding="utf-8")
    except OSError:
        return False


def environment_ready(root: Path) -> bool:
    """Whether ``pixi install`` has already run in ``root``."""
    return (root / ".pixi" / "envs" / "default").is_dir()


def inspect(
    root: Path = REPO_ROOT,
    *,
    finder: Callable[[str], str | None] = shutil.which,
    runner: Callable[..., str] = git_runner,
    pixi_home: Path = PIXI_HOME,
) -> State:
    """Report the state of the environment without touching it."""
    return State(
        pixi=which_pixi(finder=finder, pixi_home=pixi_home),
        environment=environment_ready(root),
        git=is_git_repository(root, runner=runner),
        hooks=hooks_installed(root, runner=runner),
    )


def install_environment(
    root: Path, pixi: str, *, runner: Runner = subprocess_runner, relock: bool = False
) -> int:
    """Create or refresh the environment; ``relock`` solves first."""
    try:
        if relock:
            status = runner([pixi, "lock"], cwd=root, env=pixi_env(pixi))
            if status != 0:
                return status
        return runner([pixi, "install", "--locked"], cwd=root, env=pixi_env(pixi))
    except OSError as error:
        msg = f"could not run {pixi}: {error}"
        raise RuntimeError(msg) from error


def install_hooks(root: Path, pixi: str, *, runner: Runner = subprocess_runner) -> int:
    """Install the Lefthook git hooks through the Pixi task."""
    try:
        return runner([pixi, "run", "--locked", "install-hooks"], cwd=root, env=pixi_env(pixi))
    except OSError as error:
        msg = f"could not run {pixi}: {error}"
        raise RuntimeError(msg) from error


def restore(
    root: Path = REPO_ROOT,
    *,
    runner: Runner = subprocess_runner,
    fetcher: Fetcher = url_fetcher,
    finder: Callable[[str], str | None] = shutil.which,
    git_runner_: Callable[..., str] = git_runner,
    installer: Callable[..., str | None] = install_pixi,
    pixi_home: Path = PIXI_HOME,
    version: str = PIXI_VERSION,
    relock: bool = False,
    hooks: bool = True,
) -> State:
    """Bring the repository to a ready state and return what is true afterwards.

    Raises:
        RuntimeError: if Pixi cannot be installed or the environment cannot be solved.
    """
    pixi = which_pixi(finder=finder, pixi_home=pixi_home)
    if pixi is None:
        pixi = installer(fetcher=fetcher, runner=runner, version=version, pixi_home=pixi_home)
        if pixi is None:  # pragma: no cover - install_pixi raises instead
            msg = "Pixi could not be installed"
            raise RuntimeError(msg)

    status = install_environment(root, pixi, runner=runner, relock=relock)
    if status != 0:
        msg = f"`pixi install` exited with status {status}; run with --relock to solve again"
        raise RuntimeError(msg)

    git = is_git_repository(root, runner=git_runner_)
    if hooks and git:
        status = install_hooks(root, pixi, runner=runner)
        if status != 0:
            msg = f"`pixi run install-hooks` exited with status {status}"
            raise RuntimeError(msg)

    return inspect(root, finder=lambda _name: pixi, runner=git_runner_, pixi_home=pixi_home)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point: report, or restore and report."""
    parser = argparse.ArgumentParser(
        prog="python -m automation.restore",
        description="Ensure Pixi, solve the environment and install the git hooks.",
    )
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help="repository root")
    parser.add_argument("--check", action="store_true", help="report state only, change nothing")
    parser.add_argument("--relock", action="store_true", help="run `pixi lock` before installing")
    parser.add_argument(
        "--skip-hooks", action="store_true", help="do not run `pixi run install-hooks`"
    )
    parser.add_argument("--version", default=os.environ.get("PSF_PIXI_VERSION", PIXI_VERSION))
    parser.add_argument("--json", action="store_true", help="emit the state as JSON")
    args = parser.parse_args(argv)

    if args.check:
        state = inspect(args.root)
        if args.json:
            print(json.dumps(state.to_dict(), indent=2))
        else:
            _report(state, checked=True)
        return 0 if state.complete else 1

    try:
        state = restore(
            args.root, version=args.version, relock=args.relock, hooks=not args.skip_hooks
        )
    except RuntimeError as error:
        print(f"restore: {error}")
        return 1

    if args.json:
        print(json.dumps(state.to_dict(), indent=2))
    else:
        _report(state, checked=False)
    return 0 if state.complete else 1


def _report(state: State, *, checked: bool) -> None:
    prefix = "restore" if not checked else "restore (check)"
    print(f"{prefix}: pixi {state.pixi or 'missing'}")
    print(f"{prefix}: environment {'ready' if state.environment else 'missing'}")
    if not state.git:
        print(f"{prefix}: no git checkout, Lefthook hooks skipped")
    else:
        print(f"{prefix}: hooks {'installed' if state.hooks else 'missing'}")
    verb = "is" if state.complete else "is not"
    print(f"{prefix}: repository {verb} ready")


if __name__ == "__main__":  # pragma: no cover - module entry point
    raise SystemExit(main())
