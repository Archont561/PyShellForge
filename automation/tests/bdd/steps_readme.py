"""Steps for ``automation/features/readme_generation.feature``."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest
from pytest_bdd import given, then, when

from automation.readme import generate

ATTRIBUTED = (
    "# PyShellForge\n\nWrite shell scripts in Python. Render clean Bash.\n\n"
    "_This README was generated with love by readme-md-generator._\n"
)
UNATTRIBUTED = "# PyShellForge\n\nHand written.\n"
COMMITTED = "# PyShellForge\n\nOld content.\n"


@dataclass
class FakeGenerator:
    """Stand-in for the npm generator; writes into the scratch directory."""

    content: str = ATTRIBUTED
    exit_code: int = 0
    calls: list[tuple[str, ...]] = field(default_factory=list)

    def __call__(self, command: Sequence[str], *, cwd: Path) -> int:
        self.calls.append(tuple(command))
        if self.exit_code == 0:
            (Path(cwd) / "README.md").write_text(self.content, encoding="utf-8")
        return self.exit_code


@dataclass
class ReadmeRepo:
    """A throwaway repository the script can run against."""

    root: Path
    template: Path
    package_json: Path
    target: Path
    generator: FakeGenerator

    def run(self, *, check: bool) -> int:
        """Invoke the script against this repository."""
        return generate.write_readme(
            check=check,
            template=self.template,
            package_json=self.package_json,
            targets=(self.target,),
            runner=self.generator,
        )


def _repo(root: Path) -> ReadmeRepo:
    root.mkdir(parents=True, exist_ok=True)
    template = root / "README.ejs"
    template.write_text("# <%- projectName %>\n", encoding="utf-8")
    package_json = root / "package.json"
    package_json.write_text(
        json.dumps(
            {"name": "pyshellforge", "devDependencies": {"readme-md-generator": "1.0.0"}},
            indent=2,
        ),
        encoding="utf-8",
    )
    target = root / "README.md"
    target.write_text(COMMITTED, encoding="utf-8")
    return ReadmeRepo(
        root=root,
        template=template,
        package_json=package_json,
        target=target,
        generator=FakeGenerator(),
    )


@given("a repository with the pinned generator and a README template")
def repository(tmp_path: Path, context: dict[str, Any]) -> None:
    context["repo"] = _repo(tmp_path / "repo")


@given("the generator produces a README identical to the committed one")
def identical(context: dict[str, Any]) -> None:
    repo: ReadmeRepo = context["repo"]
    repo.generator.content = ATTRIBUTED
    repo.target.write_text(ATTRIBUTED, encoding="utf-8")


@given("the generator produces a README that differs from the committed one")
def differs(context: dict[str, Any]) -> None:
    repo: ReadmeRepo = context["repo"]
    repo.generator.content = ATTRIBUTED
    repo.target.write_text(COMMITTED, encoding="utf-8")


@given("the generator produces a README without the attribution footer")
def unattributed(context: dict[str, Any]) -> None:
    repo: ReadmeRepo = context["repo"]
    repo.generator.content = UNATTRIBUTED


@given("the README template does not exist")
def no_template(context: dict[str, Any]) -> None:
    repo: ReadmeRepo = context["repo"]
    repo.template.unlink()


@given("the generator exits with a failure")
def failing_generator(context: dict[str, Any]) -> None:
    repo: ReadmeRepo = context["repo"]
    repo.generator.exit_code = 1


@when("I check the README")
def check_readme(context: dict[str, Any], capsys: pytest.CaptureFixture[str]) -> None:
    repo: ReadmeRepo = context["repo"]
    context["exit"] = repo.run(check=True)
    context["output"] = capsys.readouterr()


@when("I regenerate the README")
def regenerate_readme(context: dict[str, Any], capsys: pytest.CaptureFixture[str]) -> None:
    repo: ReadmeRepo = context["repo"]
    context["exit"] = repo.run(check=False)
    context["output"] = capsys.readouterr()


@then("the command succeeds")
def command_succeeds(context: dict[str, Any]) -> None:
    assert context["exit"] == 0


@then("the command fails")
def command_fails(context: dict[str, Any]) -> None:
    assert context["exit"] == 1


@then("the command fails with a usage error")
def command_usage_error(context: dict[str, Any]) -> None:
    assert context["exit"] == 2


@then("the output reports that the README is up to date")
def output_up_to_date(context: dict[str, Any]) -> None:
    captured = context["output"]
    assert "up to date" in captured.out


@then("the output reports that the README is out of date")
def output_out_of_date(context: dict[str, Any]) -> None:
    captured = context["output"]
    assert "out of date" in captured.err


@then("the README contains the generated content")
def readme_written(context: dict[str, Any]) -> None:
    repo: ReadmeRepo = context["repo"]
    assert repo.target.read_text(encoding="utf-8") == ATTRIBUTED


@then("the README is unchanged")
def readme_unchanged(context: dict[str, Any]) -> None:
    repo: ReadmeRepo = context["repo"]
    assert repo.target.read_text(encoding="utf-8") == COMMITTED
