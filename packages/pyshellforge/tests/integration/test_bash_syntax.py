"""Check every rendered golden script with Bash and shfmt."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from pyshellforge import Command, Comment, Echo, ShellScript, VariableAssignment

GOLDEN_DIR = Path(__file__).resolve().parents[1] / "golden"
GOLDENS = sorted(GOLDEN_DIR.glob("*.sh"))
BASH = shutil.which("bash")
SHFMT = shutil.which("shfmt")


def test_hello_script_matches_golden() -> None:
    script = ShellScript().add(
        Comment("A greeting"),
        VariableAssignment("NAME", "Ada Lovelace"),
        Echo("Hello {NAME}"),
        Command("printf", ("%s\\n", "done")),
    )
    assert script.render() == (GOLDEN_DIR / "hello.sh").read_text(encoding="utf-8")


def test_at_least_one_golden_exists() -> None:
    assert GOLDENS


@pytest.mark.skipif(BASH is None, reason="bash is required")
@pytest.mark.parametrize("script", GOLDENS, ids=lambda path: path.name)
def test_every_golden_parses_with_bash(script: Path) -> None:
    subprocess.run([str(BASH), "-n", str(script)], check=True)


@pytest.mark.skipif(BASH is None, reason="bash is required")
def test_the_rendered_script_runs() -> None:
    script = ShellScript().add(VariableAssignment("NAME", "Ada Lovelace"), Echo("Hello {NAME}"))
    result = subprocess.run(
        [str(BASH)], input=script.render(), text=True, capture_output=True, check=True
    )
    assert result.stdout == "Hello Ada Lovelace\n"


@pytest.mark.skipif(SHFMT is None, reason="shfmt is required")
@pytest.mark.parametrize("script", GOLDENS, ids=lambda path: path.name)
def test_every_golden_has_canonical_formatting(script: Path) -> None:
    subprocess.run([str(SHFMT), "-d", "-i", "4", "-ci", str(script)], check=True)


@pytest.mark.skipif(SHFMT is None, reason="shfmt is required")
def test_shfmt_rejects_a_misformatted_script(tmp_path: Path) -> None:
    script = tmp_path / "bad.sh"
    script.write_text("#!/usr/bin/env bash\nif true; then\necho hi\nfi\n", encoding="utf-8")
    result = subprocess.run([str(SHFMT), "-d", "-i", "4", "-ci", str(script)], capture_output=True)
    assert result.returncode != 0
    assert result.stdout
