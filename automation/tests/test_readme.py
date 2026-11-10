"""Tests for ``automation.readme``."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from automation.readme import generate
from automation.tests.conftest import FakeRunner

ATTRIBUTED = "# PyShellForge\n\n_This README was generated with love by readme-md-generator._\n"


def test_pinned_version_reads_dev_dependencies(repo: Path) -> None:
    assert generate.pinned_version(repo / "package.json") == "1.0.0"


@pytest.mark.parametrize("version", ["latest", "^1.0.0", "~1.0", ""])
def test_pinned_version_rejects_floating_ranges(repo: Path, version: str) -> None:
    path = repo / "package.json"
    path.write_text(
        json.dumps({"devDependencies": {"readme-md-generator": version}}), encoding="utf-8"
    )
    with pytest.raises(ValueError):
        generate.pinned_version(path)


def test_pinned_version_requires_the_dependency(repo: Path) -> None:
    path = repo / "package.json"
    path.write_text(json.dumps({"devDependencies": {}}), encoding="utf-8")
    with pytest.raises(ValueError, match="not pinned"):
        generate.pinned_version(path)


def test_generator_command_uses_npx_with_the_pin() -> None:
    command = generate.generator_command("1.0.0")
    assert command[0].startswith("npx")
    assert command[1:] == ["--yes", "readme-md-generator@1.0.0"]


def test_render_readme_runs_in_a_scratch_directory(repo: Path, runner: FakeRunner) -> None:
    result = generate.render_readme(
        template=repo / "README.ejs", package_json=repo / "package.json", runner=runner
    )
    assert result.content == "# generated\n"
    assert result.attributed is False

    command, workdir = runner.calls[0]
    assert workdir != repo
    assert not workdir.exists(), "the scratch directory must be cleaned up"
    assert "readme-md-generator@1.0.0" in command
    assert "-p" in command
    assert str(repo / "README.ejs") in command
    assert "--yes" in command and "-y" in command


def test_render_readme_copies_package_json_into_the_scratch_dir(
    repo: Path, runner: FakeRunner
) -> None:
    generate.render_readme(
        template=repo / "README.ejs", package_json=repo / "package.json", runner=runner
    )
    _, workdir = runner.calls[0]
    # The runner saw the file before cleanup; assert it was requested at all.
    assert workdir.name.startswith("psf-readme-")


def test_render_readme_requires_a_template(repo: Path, runner: FakeRunner) -> None:
    with pytest.raises(FileNotFoundError, match="template"):
        generate.render_readme(
            template=repo / "missing.ejs", package_json=repo / "package.json", runner=runner
        )


def test_render_readme_requires_metadata(repo: Path, runner: FakeRunner) -> None:
    with pytest.raises(FileNotFoundError, match="metadata"):
        generate.render_readme(
            template=repo / "README.ejs", package_json=repo / "missing.json", runner=runner
        )


def test_render_readme_reports_a_failing_generator(repo: Path) -> None:
    runner = FakeRunner(exit_code=2)
    with pytest.raises(RuntimeError, match="status 2"):
        generate.render_readme(
            template=repo / "README.ejs", package_json=repo / "package.json", runner=runner
        )


def test_render_readme_reports_a_generator_that_writes_nothing(repo: Path) -> None:
    runner = FakeRunner(write=False)
    with pytest.raises(RuntimeError, match="did not produce"):
        generate.render_readme(
            template=repo / "README.ejs", package_json=repo / "package.json", runner=runner
        )


def test_write_readme_rewrites_a_stale_file(repo: Path) -> None:
    target = repo / "README.md"
    target.write_text("old\n", encoding="utf-8")
    runner = FakeRunner(content=ATTRIBUTED)
    status = generate.write_readme(
        template=repo / "README.ejs",
        package_json=repo / "package.json",
        targets=(target,),
        runner=runner,
    )
    assert status == 0
    assert target.read_text(encoding="utf-8") == ATTRIBUTED


def test_write_readme_leaves_an_identical_file_alone(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    target = repo / "README.md"
    target.write_text(ATTRIBUTED, encoding="utf-8")
    status = generate.write_readme(
        template=repo / "README.ejs",
        package_json=repo / "package.json",
        targets=(target,),
        runner=FakeRunner(content=ATTRIBUTED),
    )
    assert status == 0
    assert "unchanged" in capsys.readouterr().out


def test_write_readme_check_passes_for_a_current_file(repo: Path) -> None:
    target = repo / "README.md"
    target.write_text(ATTRIBUTED, encoding="utf-8")
    status = generate.write_readme(
        check=True,
        template=repo / "README.ejs",
        package_json=repo / "package.json",
        targets=(target,),
        runner=FakeRunner(content=ATTRIBUTED),
    )
    assert status == 0


def test_write_readme_check_fails_for_a_stale_file(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    target = repo / "README.md"
    target.write_text("old\n", encoding="utf-8")
    status = generate.write_readme(
        check=True,
        template=repo / "README.ejs",
        package_json=repo / "package.json",
        targets=(target,),
        runner=FakeRunner(content=ATTRIBUTED),
    )
    assert status == 1
    assert "out of date" in capsys.readouterr().err
    assert target.read_text(encoding="utf-8") == "old\n"


def test_write_readme_rejects_output_without_attribution(repo: Path) -> None:
    status = generate.write_readme(
        template=repo / "README.ejs",
        package_json=repo / "package.json",
        targets=(repo / "README.md",),
        runner=FakeRunner(content="# hand written\n"),
    )
    assert status == 1


def test_write_readme_maps_missing_inputs_to_a_usage_error(repo: Path) -> None:
    status = generate.write_readme(
        template=repo / "missing.ejs",
        package_json=repo / "package.json",
        targets=(repo / "README.md",),
        runner=FakeRunner(),
    )
    assert status == 2


def test_main_accepts_check_flag(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        generate,
        "render_readme",
        lambda **_: generate.ReadmeResult(content=ATTRIBUTED, command=("npx",)),
    )
    target = repo / "README.md"
    target.write_text(ATTRIBUTED, encoding="utf-8")
    monkeypatch.setattr(generate, "TARGETS", (target,))
    assert generate.main(["--check", "--template", str(repo / "README.ejs")]) == 0


def test_main_reports_a_missing_template(tmp_path: Path) -> None:
    assert generate.main(["--template", str(tmp_path / "nope.ejs")]) == 2


@pytest.mark.skipif(sys.platform == "win32", reason="npx wrapper naming differs on Windows")
def test_generator_command_is_platform_aware() -> None:
    assert generate.generator_command("1.0.0")[0] == "npx"


def test_project_depth_counts_directories_below_the_root() -> None:
    assert generate.project_depth(generate.REPO_ROOT / "README.md") == 0
    assert (
        generate.project_depth(generate.REPO_ROOT / "packages" / "pyshellforge" / "README.md") == 2
    )
    assert generate.project_depth(Path("/elsewhere/README.md")) == 0


def test_relocate_links_rebases_only_relative_targets() -> None:
    content = "see [docs](docs/README.md), [site](https://example.com/x) and [top](#what-it-is)"
    relocated = generate.relocate_links(content, 1)
    assert "[docs](../docs/README.md)" in relocated
    assert "[site](https://example.com/x)" in relocated
    assert "[top](#what-it-is)" in relocated


def test_relocate_links_at_the_root_changes_nothing() -> None:
    content = "[docs](docs/README.md)"
    assert generate.relocate_links(content, 0) == content


LINKED = "# P\n\n[docs](docs/README.md)\n\n_This README was generated for a test._\n"


def test_write_readme_writes_every_target(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = repo / "README.md"
    nested = repo / "pyshellforge" / "README.md"
    status = generate.write_readme(
        template=repo / "README.ejs",
        package_json=repo / "package.json",
        targets=(root, nested),
        runner=FakeRunner(content=LINKED),
    )
    assert status == 0
    # Both copies carry the same text: rebasing only kicks in for a target that
    # really sits below the repository root, which a temporary directory is not.
    assert root.read_text(encoding="utf-8") == LINKED
    assert nested.read_text(encoding="utf-8") == LINKED
    assert "written" in capsys.readouterr().out


def test_check_reports_every_copy(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = repo / "README.md"
    nested = repo / "pyshellforge" / "README.md"
    nested.parent.mkdir()
    root.write_text(LINKED, encoding="utf-8")
    nested.write_text(LINKED, encoding="utf-8")
    status = generate.write_readme(
        check=True,
        template=repo / "README.ejs",
        package_json=repo / "package.json",
        targets=(root, nested),
        runner=FakeRunner(content=LINKED),
    )
    assert status == 0
    out = capsys.readouterr().out
    assert out.count("is up to date") == 2
