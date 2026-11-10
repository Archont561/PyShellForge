"""Shared fixtures for the repository-script tests."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

import pytest


@dataclass
class FakeRunner:
    """Records invocations and optionally writes a README into the workdir."""

    content: str = "# generated\n"
    exit_code: int = 0
    write: bool = True
    calls: list[tuple[tuple[str, ...], Path]] = field(default_factory=list)

    def __call__(self, command: Sequence[str], *, cwd: Path) -> int:
        self.calls.append((tuple(command), Path(cwd)))
        if self.write:
            (Path(cwd) / "README.md").write_text(self.content, encoding="utf-8")
        return self.exit_code


@pytest.fixture
def runner() -> FakeRunner:
    return FakeRunner()


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A minimal stand-in repository: package.json plus a template."""
    (tmp_path / "package.json").write_text(
        json.dumps({"name": "pyshellforge", "devDependencies": {"readme-md-generator": "1.0.0"}}),
        encoding="utf-8",
    )
    (tmp_path / "README.ejs").write_text("# <%= projectName %>\n", encoding="utf-8")
    return tmp_path
