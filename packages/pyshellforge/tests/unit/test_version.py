"""``pyshellforge.VERSION`` has one source of truth: ``pyproject.toml``.

The package ships one module, so these tests are the whole product suite: the
attribute, the resolution order behind it, and the fallbacks that keep
``import pyshellforge`` working outside a source checkout.
"""

from __future__ import annotations

import re
import tomllib
from importlib.metadata import PackageNotFoundError
from pathlib import Path

import pytest

import pyshellforge

ROOT = Path(__file__).resolve().parents[2]
PYPROJECT = ROOT / "pyproject.toml"

SEMVER = re.compile(r"^\d+\.\d+\.\d+([.-]?[0-9A-Za-z.]+)?$")


def pyproject_version() -> str:
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    return str(data["project"]["version"])


def write_pyproject(directory: Path, version: str | None) -> Path:
    """Write a minimal ``pyproject.toml`` in ``directory`` and return its path."""
    directory.mkdir(parents=True, exist_ok=True)
    project = '[project]\nname = "sample"\n'
    if version is not None:
        project += f'version = "{version}"\n'
    path = directory / "pyproject.toml"
    path.write_text(project, encoding="utf-8")
    return path


class TestThePackageAttribute:
    def test_version_matches_pyproject(self) -> None:
        assert pyproject_version() == pyshellforge.VERSION

    def test_version_is_semver_shaped(self) -> None:
        assert SEMVER.match(pyshellforge.VERSION), pyshellforge.VERSION

    def test_the_module_exports_only_the_version(self) -> None:
        assert pyshellforge.__all__ == ["VERSION"]


class TestReadVersion:
    def test_reads_a_static_version(self, tmp_path: Path) -> None:
        assert pyshellforge.read_version(write_pyproject(tmp_path, "1.2.3")) == "1.2.3"

    def test_strips_surrounding_whitespace(self, tmp_path: Path) -> None:
        path = tmp_path / "pyproject.toml"
        path.write_text('[project]\nversion = " 2.0.0 "\n', encoding="utf-8")
        assert pyshellforge.read_version(path) == "2.0.0"

    def test_missing_file(self, tmp_path: Path) -> None:
        assert pyshellforge.read_version(tmp_path / "absent.toml") is None

    def test_unparsable_file(self, tmp_path: Path) -> None:
        path = tmp_path / "pyproject.toml"
        path.write_text("[project\nversion = 1\n", encoding="utf-8")
        assert pyshellforge.read_version(path) is None

    def test_file_that_is_not_utf8(self, tmp_path: Path) -> None:
        path = tmp_path / "pyproject.toml"
        path.write_bytes(b'[project]\nversion = "\xff\xfe"\n')
        assert pyshellforge.read_version(path) is None

    def test_no_project_table(self, tmp_path: Path) -> None:
        path = tmp_path / "pyproject.toml"
        path.write_text("[tool.ruff]\nline-length = 100\n", encoding="utf-8")
        assert pyshellforge.read_version(path) is None

    def test_project_without_a_static_version(self, tmp_path: Path) -> None:
        assert pyshellforge.read_version(write_pyproject(tmp_path, None)) is None

    @pytest.mark.parametrize("value", ["", "next", "1.0-beta!", "caf\u00e9"])
    def test_a_value_that_does_not_look_like_a_version(self, tmp_path: Path, value: str) -> None:
        path = tmp_path / "pyproject.toml"
        path.write_text(f'[project]\nversion = "{value}"\n', encoding="utf-8")
        assert pyshellforge.read_version(path) is None


class TestFindPyproject:
    def test_finds_the_repository_manifest(self) -> None:
        assert pyshellforge.find_pyproject() == PYPROJECT

    def test_walks_up_from_a_nested_file(self, tmp_path: Path) -> None:
        write_pyproject(tmp_path, "9.9.9")
        nested = tmp_path / "a" / "b"
        nested.mkdir(parents=True)
        target = nested / "module.py"
        target.write_text("", encoding="utf-8")
        assert pyshellforge.find_pyproject(target) == tmp_path / "pyproject.toml"

    def test_a_directory_start_is_accepted(self, tmp_path: Path) -> None:
        write_pyproject(tmp_path, "9.9.9")
        assert pyshellforge.find_pyproject(tmp_path) == tmp_path / "pyproject.toml"

    def test_returns_none_when_no_manifest_exists(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(pyshellforge, "PYPROJECT_NAME", "no-such-manifest.toml")
        assert pyshellforge.find_pyproject() is None


class TestInstalledVersion:
    def test_uses_distribution_metadata(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(pyshellforge, "version", lambda dist: "3.2.1")
        assert pyshellforge.installed_version() == "3.2.1"

    def test_a_missing_distribution_is_not_an_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def missing(dist: str) -> str:
            raise PackageNotFoundError(dist)

        monkeypatch.setattr(pyshellforge, "version", missing)
        assert pyshellforge.installed_version() is None


class TestResolutionOrder:
    def test_pyproject_wins_over_metadata(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        manifest = write_pyproject(tmp_path, "4.5.6")
        monkeypatch.setattr(pyshellforge, "find_pyproject", lambda start=None: manifest)
        monkeypatch.setattr(pyshellforge, "installed_version", lambda: "0.0.1")
        assert pyshellforge.resolve_version() == "4.5.6"

    def test_metadata_is_used_without_a_checkout(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(pyshellforge, "find_pyproject", lambda start=None: None)
        monkeypatch.setattr(pyshellforge, "installed_version", lambda: "7.8.9")
        assert pyshellforge.resolve_version() == "7.8.9"

    def test_an_unreadable_manifest_falls_through_to_metadata(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        manifest = write_pyproject(tmp_path, None)
        monkeypatch.setattr(pyshellforge, "find_pyproject", lambda start=None: manifest)
        monkeypatch.setattr(pyshellforge, "installed_version", lambda: "7.8.9")
        assert pyshellforge.resolve_version() == "7.8.9"

    def test_the_constant_is_the_last_resort(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(pyshellforge, "find_pyproject", lambda start=None: None)
        monkeypatch.setattr(pyshellforge, "installed_version", lambda: None)
        assert pyshellforge.resolve_version() == pyshellforge.FALLBACK_VERSION
