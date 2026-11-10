"""Build the release distributions, or refuse to build them at all.

Releasing is the one operation in this repository that cannot be undone: PyPI
rejects a version number it has already seen, so a build made from the wrong
commit can burn a version for good. This script therefore does the checking
before it does the building:

1. the tag, when one is given (``GITHUB_REF_NAME`` in CI, ``--ref`` locally), must
   match ``[project].version`` in ``pyproject.toml``;
2. ``dist/`` is emptied, so a stale artifact cannot ride along into an upload;
3. ``python -m build`` produces the sdist and the wheel;
4. ``twine check`` validates both.

The structure mirrors the release workflow of the sibling repository
``Archont561/rude-clean-code``: a build job with the version guard and a separate
publish job that only exchanges an OIDC token with PyPI. The guard lives here, in
Python, because every other repository script is Python and is tested — the shell
version of this file existed only because that repository keeps its build logic in
``automation/``.

Usage::

    python -m automation.release                   # tag check (if set), build, twine check
    python -m automation.release --check           # tag check only, exit 1 on a mismatch
    python -m automation.release --ref v0.1.0      # as GitHub would pass it
    python -m automation.release --skip-tag-check  # local iteration on the build

``python -m automation.release --check`` is what ``pixi run check-release`` runs: it
needs neither ``build`` nor a clean ``dist/``.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

#: Repository root, derived from this file (``automation/release/build.py``).
REPO_ROOT = Path(__file__).resolve().parents[2]

#: The distribution lives in its own directory inside the repository.
PROJECT_DIR_NAME = "pyshellforge"

#: Manifest that holds the single source of truth for the version.
PYPROJECT_NAME = "pyproject.toml"

#: Where the distributions are written (repository root, outside the project).
DIST_NAME = "dist"

#: Environment variable GitHub sets to the tag when a workflow runs on one.
CI_REF_ENV = "GITHUB_REF_NAME"

#: A runner executes a command and returns its stdout.
Runner = Callable[[Sequence[str]], str]


class ReleaseError(RuntimeError):
    """Raised when the release must not continue."""


@dataclass(frozen=True)
class Plan:
    """What the release build is about to do, printed before it happens."""

    version: str
    tag: str | None
    #: Whether a tag was present and compared; a missing tag is not a pass.
    tag_checked: bool
    dist: str

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serialisable representation."""
        return asdict(self)


def subprocess_runner(command: Sequence[str]) -> str:
    """Run ``command`` in the repository root and return its stdout."""
    completed = subprocess.run(
        list(command),
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout


def read_package_version(
    pyproject: str | Path = REPO_ROOT / PROJECT_DIR_NAME / PYPROJECT_NAME,
) -> str:
    """Return ``[project].version`` from ``pyproject.toml``."""
    path = Path(pyproject)
    try:
        import tomllib

        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise ReleaseError(f"cannot read {path}: {error}") from error
    except ValueError as error:  # tomllib.TOMLDecodeError is a ValueError
        raise ReleaseError(f"{path} is not valid TOML: {error}") from error
    project = data.get("project")
    if not isinstance(project, dict):
        raise ReleaseError(f"{path} has no [project] table")
    version = project.get("version")
    if not isinstance(version, str) or not version:
        raise ReleaseError(f"{path} has no static [project].version")
    return version


def tag_of(ref: str) -> str:
    """Return the tag in ``ref``, dropping any ``refs/tags/`` prefix and the ``v``."""
    name = ref.strip()
    if name.startswith("refs/tags/"):
        name = name[len("refs/tags/") :]
    return name[1:] if name.startswith("v") else name


def verify_tag(ref: str | None, version: str) -> str | None:
    """Return the tag for ``ref``; raise when it disagrees with ``version``.

    A missing ref is not an error: it means the build is not running on a tag,
    which is the local case, and the guard simply does not apply.
    """
    if not ref or not ref.strip():
        return None
    tag = tag_of(ref)
    if tag != version:
        raise ReleaseError(
            f"tag {ref!r} does not match the package version {version!r}; "
            "bump [project].version or retag the commit"
        )
    return tag


def clean_distributions(dist: Path) -> None:
    """Delete ``dist`` so no earlier artifact can be uploaded by accident."""
    if dist.exists():
        shutil.rmtree(dist)
    dist.mkdir(parents=True)


def build_distributions(dist: Path, *, runner: Runner | None = None) -> list[Path]:
    """Build the sdist and the wheel into ``dist`` and return what appeared."""
    run = runner or subprocess_runner
    run(["python", "-m", "build", "--outdir", str(dist), PROJECT_DIR_NAME])
    artifacts = sorted(path for path in dist.iterdir() if path.is_file())
    if not artifacts:
        raise ReleaseError(f"{dist} is empty after the build")
    return artifacts


def check_distributions(artifacts: Sequence[Path], *, runner: Runner | None = None) -> None:
    """Validate the distributions with ``twine check``."""
    if not artifacts:
        raise ReleaseError("nothing to check")
    run = runner or subprocess_runner
    run(["python", "-m", "twine", "check", *(str(path) for path in artifacts)])


def release(
    *,
    ref: str | None = None,
    dist: Path | str = REPO_ROOT / DIST_NAME,
    pyproject: str | Path = REPO_ROOT / PROJECT_DIR_NAME / PYPROJECT_NAME,
    check_only: bool = False,
    skip_tag_check: bool = False,
    runner: Runner | None = None,
) -> tuple[Plan, list[Path]]:
    """Run the release build and return the plan it followed and its artifacts."""
    version = read_package_version(pyproject)
    tag = None if skip_tag_check else verify_tag(ref, version)
    directory = Path(dist)
    # ``tag_checked`` reports whether a tag was actually compared, so a local run
    # without one is visible in the output instead of looking like a pass.
    plan = Plan(version=version, tag=tag, tag_checked=tag is not None, dist=str(directory))
    if check_only:
        return plan, []
    clean_distributions(directory)
    artifacts = build_distributions(directory, runner=runner)
    check_distributions(artifacts, runner=runner)
    return plan, artifacts


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point: guard, build, check. Exit 1 when the guard fails."""
    parser = argparse.ArgumentParser(
        prog="python -m automation.release",
        description="Build the release distributions, guarded by the tag and the version.",
    )
    parser.add_argument("--ref", default=None, help=f"the tag, as {CI_REF_ENV} would carry it")
    parser.add_argument("--dist", default=str(REPO_ROOT / DIST_NAME), help="output directory")
    parser.add_argument(
        "--pyproject",
        default=str(REPO_ROOT / PROJECT_DIR_NAME / PYPROJECT_NAME),
        help="manifest",
    )
    parser.add_argument("--check", action="store_true", help="verify the tag only, build nothing")
    parser.add_argument(
        "--skip-tag-check", action="store_true", help="build without comparing the tag"
    )
    parser.add_argument("--json", action="store_true", help="emit the plan as JSON")
    args = parser.parse_args(argv)

    ref = args.ref if args.ref is not None else os.environ.get(CI_REF_ENV)
    try:
        plan, artifacts = release(
            ref=ref,
            dist=args.dist,
            pyproject=args.pyproject,
            check_only=args.check,
            skip_tag_check=args.skip_tag_check,
        )
    except ReleaseError as error:
        print(f"release: {error}")
        return 1
    except subprocess.CalledProcessError as error:  # pragma: no cover - depends on the tools
        print(f"release: {' '.join(error.cmd)} failed with status {error.returncode}")
        return 1

    if args.json:
        print(
            json.dumps({**plan.to_dict(), "artifacts": [str(path) for path in artifacts]}, indent=2)
        )
    else:
        scope = f"tag {plan.tag}" if plan.tag else "no tag, guard skipped"
        prefix = "release (check)" if args.check else "release"
        print(f"{prefix}: version {plan.version}, {scope}")
        if not args.check:
            for artifact in artifacts:
                print(f"release: built {artifact}")
            print("release: distributions checked")
    return 0


if __name__ == "__main__":  # pragma: no cover - module entry point
    raise SystemExit(main())
