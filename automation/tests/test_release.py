"""Tests for ``automation.release``."""

from __future__ import annotations

import json
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

import pytest

from automation.release import build

PYPROJECT = build.REPO_ROOT / build.PROJECT_DIR_NAME / "pyproject.toml"


def write_manifest(directory: Path, version: str | None = "1.2.3", *, project: bool = True) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    text = ""
    if project:
        text = '[project]\nname = "sample"\n'
        if version is not None:
            text += f'version = "{version}"\n'
    path = directory / "pyproject.toml"
    path.write_text(text, encoding="utf-8")
    return path


class RecordingRunner:
    """A runner that records commands and lays down the artifacts ``build`` makes."""

    def __init__(
        self, *, artifacts: Sequence[str] = ("pkg-1.2.3.tar.gz", "pkg-1.2.3-py3-none-any.whl")
    ):
        self.commands: list[list[str]] = []
        self.artifacts = artifacts

    def __call__(self, command: Sequence[str]) -> str:
        self.commands.append(list(command))
        if "build" in command:
            outdir = Path(command[command.index("--outdir") + 1])
            for name in self.artifacts:
                (outdir / name).write_text("artifact", encoding="utf-8")
        return ""


# -- the runner --------------------------------------------------------------
def test_the_runner_returns_stdout() -> None:
    output = build.subprocess_runner([sys.executable, "-c", "print('built')"])
    assert output.strip() == "built"


def test_the_runner_fails_loudly() -> None:
    with pytest.raises(subprocess.CalledProcessError):
        build.subprocess_runner([sys.executable, "-c", "raise SystemExit(3)"])


# -- the manifest ------------------------------------------------------------
def test_reads_the_repository_version() -> None:
    assert build.read_package_version(PYPROJECT) == "0.1.0"


def test_missing_manifest(tmp_path: Path) -> None:
    with pytest.raises(build.ReleaseError, match="cannot read"):
        build.read_package_version(tmp_path / "absent.toml")


def test_unparsable_manifest(tmp_path: Path) -> None:
    path = tmp_path / "pyproject.toml"
    path.write_text("[project\nversion = 1\n", encoding="utf-8")
    with pytest.raises(build.ReleaseError, match="not valid TOML"):
        build.read_package_version(path)


def test_manifest_without_a_project_table(tmp_path: Path) -> None:
    path = write_manifest(tmp_path, project=False)
    with pytest.raises(build.ReleaseError, match=r"no \[project\] table"):
        build.read_package_version(path)


def test_manifest_without_a_static_version(tmp_path: Path) -> None:
    path = write_manifest(tmp_path, version=None)
    with pytest.raises(build.ReleaseError, match="no static"):
        build.read_package_version(path)


# -- the tag guard -----------------------------------------------------------
@pytest.mark.parametrize(
    ("ref", "expected"),
    [
        ("v0.1.0", "0.1.0"),
        ("0.1.0", "0.1.0"),
        ("refs/tags/v1.2.3", "1.2.3"),
        ("refs/tags/1.2.3", "1.2.3"),
        ("v1.2.3-rc1", "1.2.3-rc1"),
    ],
)
def test_tag_of(ref: str, expected: str) -> None:
    assert build.tag_of(ref) == expected


def test_a_matching_tag_is_accepted() -> None:
    assert build.verify_tag("v0.1.0", "0.1.0") == "0.1.0"


@pytest.mark.parametrize("ref", [None, "", "   "])
def test_no_tag_means_no_guard(ref: str | None) -> None:
    assert build.verify_tag(ref, "0.1.0") is None


def test_a_tag_that_disagrees_is_rejected() -> None:
    with pytest.raises(build.ReleaseError, match="does not match"):
        build.verify_tag("v9.9.9", "0.1.0")


# -- the build ---------------------------------------------------------------
def test_cleaning_removes_a_stale_artifact(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "stale.tar.gz").write_text("old", encoding="utf-8")
    build.clean_distributions(dist)
    assert dist.is_dir()
    assert list(dist.iterdir()) == []


def test_cleaning_creates_the_directory(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    build.clean_distributions(dist)
    assert dist.is_dir()


def test_the_build_returns_what_appeared(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    dist.mkdir()
    runner = RecordingRunner()
    artifacts = build.build_distributions(dist, runner=runner)
    assert [path.name for path in artifacts] == ["pkg-1.2.3-py3-none-any.whl", "pkg-1.2.3.tar.gz"]
    assert runner.commands[0][:3] == ["python", "-m", "build"]


def test_a_build_that_produces_nothing_is_an_error(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    dist.mkdir()
    with pytest.raises(build.ReleaseError, match="is empty"):
        build.build_distributions(dist, runner=RecordingRunner(artifacts=()))


def test_twine_checks_every_artifact(tmp_path: Path) -> None:
    artifacts = [tmp_path / "a.tar.gz", tmp_path / "b.whl"]
    runner = RecordingRunner()
    build.check_distributions(artifacts, runner=runner)
    command = runner.commands[0]
    assert command[:4] == ["python", "-m", "twine", "check"]
    assert command[4:] == [str(path) for path in artifacts]


def test_twine_with_nothing_to_check_is_an_error() -> None:
    with pytest.raises(build.ReleaseError, match="nothing to check"):
        build.check_distributions([], runner=RecordingRunner())


# -- the whole release -------------------------------------------------------
def test_release_builds_and_checks(tmp_path: Path) -> None:
    runner = RecordingRunner()
    plan, artifacts = build.release(
        build.Request(
            ref="v1.2.3", dist=tmp_path / "dist", pyproject=write_manifest(tmp_path), runner=runner
        )
    )
    assert plan.version == "1.2.3"
    assert plan.tag == "1.2.3"
    assert plan.tag_checked is True
    assert len(artifacts) == 2
    assert [command[2] for command in runner.commands] == ["build", "twine"]


def test_a_tag_mismatch_builds_nothing(tmp_path: Path) -> None:
    runner = RecordingRunner()
    with pytest.raises(build.ReleaseError, match="does not match"):
        build.release(
            build.Request(
                ref="v9.9.9",
                dist=tmp_path / "dist",
                pyproject=write_manifest(tmp_path),
                runner=runner,
            )
        )
    assert runner.commands == []


def test_check_only_writes_nothing(tmp_path: Path) -> None:
    runner = RecordingRunner()
    dist = tmp_path / "dist"
    plan, artifacts = build.release(
        build.Request(
            ref="v1.2.3",
            dist=dist,
            pyproject=write_manifest(tmp_path),
            check_only=True,
            runner=runner,
        )
    )
    assert artifacts == []
    assert runner.commands == []
    assert not dist.exists()
    assert plan.tag == "1.2.3"


def test_the_tag_check_can_be_skipped(tmp_path: Path) -> None:
    runner = RecordingRunner()
    plan, _ = build.release(
        build.Request(
            ref="v9.9.9",
            dist=tmp_path / "dist",
            pyproject=write_manifest(tmp_path),
            skip_tag_check=True,
            runner=runner,
        )
    )
    assert plan.tag is None
    assert plan.tag_checked is False


# -- the command line --------------------------------------------------------
def test_main_checks_the_tag(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest = write_manifest(tmp_path)
    assert build.main(["--check", "--ref", "v1.2.3", "--pyproject", str(manifest)]) == 0
    assert "release (check): version 1.2.3, tag 1.2.3" in capsys.readouterr().out


def test_main_reads_the_ci_environment(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest = write_manifest(tmp_path)
    monkeypatch.setenv(build.CI_REF_ENV, "v1.2.3")
    assert build.main(["--check", "--pyproject", str(manifest)]) == 0
    assert "tag 1.2.3" in capsys.readouterr().out


def test_a_check_run_says_nothing_about_building(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    manifest = write_manifest(tmp_path)
    assert build.main(["--check", "--ref", "v1.2.3", "--pyproject", str(manifest)]) == 0
    out = capsys.readouterr().out
    assert "distributions checked" not in out
    assert "built" not in out


def test_main_reports_a_mismatch(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    manifest = write_manifest(tmp_path)
    assert build.main(["--check", "--ref", "v9.9.9", "--pyproject", str(manifest)]) == 1
    assert "does not match" in capsys.readouterr().out


def test_main_emits_json(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest = write_manifest(tmp_path)
    runner = RecordingRunner()
    monkeypatch.setattr(build, "subprocess_runner", runner)
    code = build.main(
        [
            "--ref",
            "v1.2.3",
            "--dist",
            str(tmp_path / "dist"),
            "--pyproject",
            str(manifest),
            "--json",
        ]
    )
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["version"] == "1.2.3"
    assert payload["tag"] == "1.2.3"
    assert len(payload["artifacts"]) == 2


def test_main_builds_and_reports_each_artifact(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest = write_manifest(tmp_path)
    monkeypatch.setattr(build, "subprocess_runner", RecordingRunner())
    code = build.main(
        ["--ref", "v1.2.3", "--dist", str(tmp_path / "dist"), "--pyproject", str(manifest)]
    )
    out = capsys.readouterr().out
    assert code == 0
    assert "release: built" in out
    assert "release: distributions checked" in out
