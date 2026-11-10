"""Steps for ``automation/features/release_build.feature``."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

from pytest_bdd import given, then, when

from automation.release import build

ARTIFACTS = ("sample-1.2.3-py3-none-any.whl", "sample-1.2.3.tar.gz")


class FakeBuilder:
    """Records the commands and lays down the files ``python -m build`` writes."""

    def __init__(self) -> None:
        self.commands: list[list[str]] = []

    def __call__(self, command: Sequence[str]) -> str:
        self.commands.append(list(command))
        if "build" in command:
            outdir = Path(command[command.index("--outdir") + 1])
            for name in ARTIFACTS:
                (outdir / name).write_text("artifact", encoding="utf-8")
        return ""


def _prepare(context: dict[str, Any], tmp_path: Path, *, ref: str | None) -> None:
    manifest = tmp_path / "pyproject.toml"
    manifest.write_text('[project]\nname = "sample"\nversion = "1.2.3"\n', encoding="utf-8")
    context["ref"] = ref
    context["pyproject"] = manifest
    context["dist"] = tmp_path / "dist"
    context["builder"] = FakeBuilder()


@given("a package version of 1.2.3 and the tag v1.2.3")
def matching_tag(context: dict[str, Any], tmp_path: Path) -> None:
    _prepare(context, tmp_path, ref="v1.2.3")


@given("a package version of 1.2.3 and the tag v1.2.4")
def mismatched_tag(context: dict[str, Any], tmp_path: Path) -> None:
    _prepare(context, tmp_path, ref="v1.2.4")


@given("a package version of 1.2.3 and no tag")
def no_tag(context: dict[str, Any], tmp_path: Path) -> None:
    _prepare(context, tmp_path, ref=None)


@given("a stale artifact in the distribution directory")
def stale_artifact(context: dict[str, Any], tmp_path: Path) -> None:
    _prepare(context, tmp_path, ref="v1.2.3")
    dist = Path(str(context["dist"]))
    dist.mkdir(parents=True)
    stale = dist / "stale-0.0.1.tar.gz"
    stale.write_text("old", encoding="utf-8")
    context["stale"] = stale


def _release(context: dict[str, Any], *, check_only: bool = False) -> None:
    context["error"] = None
    context["artifacts"] = []
    try:
        plan, artifacts = build.release(
            ref=context["ref"],
            dist=Path(str(context["dist"])),
            pyproject=Path(str(context["pyproject"])),
            check_only=check_only,
            runner=context["builder"],
        )
    except build.ReleaseError as error:
        context["error"] = str(error)
        return
    context["plan"] = plan
    context["artifacts"] = artifacts


@when("I build the release")
def build_the_release(context: dict[str, Any]) -> None:
    _release(context)


@when("I check the release tag only")
def check_the_tag(context: dict[str, Any]) -> None:
    _release(context, check_only=True)


@then("the distributions are built and checked")
def built_and_checked(context: dict[str, Any]) -> None:
    assert context["error"] is None, context["error"]
    artifacts = context["artifacts"]
    assert [path.name for path in artifacts] == list(ARTIFACTS)
    commands = context["builder"].commands
    assert [command[2] for command in commands] == ["build", "twine"]


@then("the release is refused before anything is built")
def refused(context: dict[str, Any]) -> None:
    assert context["error"] is not None
    assert "does not match" in str(context["error"])
    assert context["builder"].commands == []


@then("the tag guard reports that it was skipped")
def guard_skipped(context: dict[str, Any]) -> None:
    plan = context["plan"]
    assert plan.tag is None
    assert plan.tag_checked is False


@then("the stale artifact is gone from the distribution directory")
def stale_gone(context: dict[str, Any]) -> None:
    stale = Path(str(context["stale"]))
    assert not stale.exists()
    dist = Path(str(context["dist"]))
    assert sorted(path.name for path in dist.iterdir()) == list(ARTIFACTS)


@then("no distribution directory exists")
def no_dist(context: dict[str, Any]) -> None:
    assert not Path(str(context["dist"])).exists()
