"""Steps for the Bash rendering scenario."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest
from pytest_bdd import given, then, when

from pyshellforge import Command, Comment, Echo, ShellScript, VariableAssignment


@given("a script that assigns a greeting name", target_fixture="script")
def greeting_script() -> ShellScript:
    return ShellScript().add(
        Comment("A greeting"),
        VariableAssignment("NAME", "Ada Lovelace"),
        Echo("Hello {NAME}"),
        Command("printf", ("%s\\n", "done")),
    )


@when("the script is rendered as Bash", target_fixture="rendered")
def render_script(script: ShellScript) -> str:
    return script.render()


@then("the generated Bash matches the greeting golden file")
def matches_golden(rendered: str) -> None:
    golden = Path(__file__).resolve().parents[1] / "golden" / "hello.sh"
    assert rendered == golden.read_text(encoding="utf-8")


@then("the generated Bash prints the greeting")
def prints_greeting(rendered: str) -> None:
    bash = shutil.which("bash")
    if bash is None:
        pytest.skip("bash is required")
    result = subprocess.run([bash], input=rendered, text=True, capture_output=True, check=True)
    assert result.stdout == "Hello Ada Lovelace\ndone\n"
