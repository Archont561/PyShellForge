"""The Bash foundation: literals, nodes, interpolation and dispatch."""

from __future__ import annotations

import shutil
import subprocess
from collections.abc import Sequence

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from pyshellforge import (
    BashRenderer,
    Command,
    Comment,
    Echo,
    InterpolationError,
    Node,
    ShellScript,
    UnsupportedNodeError,
    VariableAssignment,
)
from pyshellforge.renderers.bash import quote_literal

BASH = shutil.which("bash")


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("hello", "hello"),
        ("", "''"),
        ("two words", "'two words'"),
        ("it's", "'it'\\''s'"),
        ("$HOME", "'$HOME'"),
        ("x\ny", "$'x\\x0ay'"),
        ("\x7f", "$'\\x7f'"),
    ],
)
def test_literal_quoting(value: str, expected: str) -> None:
    assert quote_literal(value) == expected


def test_null_cannot_be_quoted() -> None:
    with pytest.raises(ValueError, match="NUL"):
        quote_literal("a\0b")


@pytest.mark.skipif(BASH is None, reason="bash is required")
@settings(max_examples=100, deadline=None)
@given(
    st.text(
        alphabet=st.characters(blacklist_categories=("Cs",), blacklist_characters="\0"), max_size=80
    )
)
def test_literal_quoting_round_trips(value: str) -> None:
    result = subprocess.run(
        [str(BASH), "-c", "printf %s " + quote_literal(value)],
        capture_output=True,
        check=True,
    )
    assert result.stdout.decode("utf-8") == value


def test_script_renders_nodes_and_trims_comment_whitespace() -> None:
    script = ShellScript(renderer=BashRenderer()).add(
        Comment("heading  \n\nnext"),
        VariableAssignment("NAME", "a b"),
        Command("printf", ("%s\\n", "hello world")),
        Echo("Hello {NAME}"),
    )
    assert script.render() == (
        "#!/usr/bin/env bash\n# heading\n#\n# next\nNAME='a b'\n"
        "printf '%s\\n' 'hello world'\nprintf '%s\\n' \"Hello ${NAME}\"\n"
    )


def test_a_renderer_can_be_injected_and_receives_a_snapshot() -> None:
    class Renderer:
        def render(self, nodes: Sequence[Node]) -> str:
            return str(len(nodes))

    script = ShellScript(Renderer()).add(Comment("hello"))
    assert script.render() == "1"


def test_non_nodes_are_rejected_atomically() -> None:
    script = ShellScript()
    with pytest.raises(TypeError, match="shell nodes"):
        script.add(Comment("ok"), "bad")  # type: ignore[arg-type]
    assert script.render() == "#!/usr/bin/env bash\n"


def test_unsupported_node_identifies_node_and_target() -> None:
    class Other(Node):
        pass

    with pytest.raises(UnsupportedNodeError, match=r"Other.*bash"):
        ShellScript().add(Other()).render()


@pytest.mark.parametrize("name", ["", "1x", "a-b", "A;echo hacked", "a b", "a\nX"])
def test_invalid_assignment_names_are_rejected(name: str) -> None:
    with pytest.raises(ValueError, match="invalid variable name"):
        ShellScript().add(VariableAssignment(name, "x")).render()


@pytest.mark.parametrize("text", ["\0", "\r"])
def test_invalid_comment_contents_are_rejected(text: str) -> None:
    with pytest.raises(ValueError, match="comments cannot"):
        ShellScript().add(Comment(text)).render()


def test_empty_command_name_is_rejected() -> None:
    with pytest.raises(ValueError, match="command name"):
        ShellScript().add(Command("")).render()


@pytest.mark.parametrize("name", ["if", "FOO=bar"])
def test_command_names_cannot_become_shell_syntax(name: str) -> None:
    assert ShellScript().add(Command(name)).render().endswith(f"'{name}'\n")


@pytest.mark.parametrize(
    "template",
    [
        "{MISSING}",
        "{NAME!r}",
        "{NAME!}",
        "{NAME:}",
        "{NAME:>10}",
        "{NAME.attr}",
        "{NAME[0]}",
        "{}",
        "{NAME",
        "NAME}",
        "{NAME!q!r}",
        "\0",
        "\n",
    ],
)
def test_invalid_interpolation_is_rejected(template: str) -> None:
    script = ShellScript().add(VariableAssignment("NAME", "x"), Echo(template))
    with pytest.raises(InterpolationError):
        script.render()


def test_echo_literal_and_braces_are_escaped() -> None:
    script = ShellScript().add(VariableAssignment("NAME", "x"), Echo('{{$HOME}} "`\\ {NAME}'))
    assert script.render().endswith('printf \'%s\\n\' "{\\$HOME} \\"\\`\\\\ ${NAME}"\n')


@pytest.mark.skipif(BASH is None, reason="bash is required")
def test_runtime_quote_and_literal_text_cannot_inject_commands() -> None:
    value = "'$(printf hacked); *"
    script = ShellScript().add(
        VariableAssignment("VALUE", value), Echo("value={VALUE} quoted={VALUE!q}")
    )
    output = subprocess.run(
        [str(BASH)], input=script.render(), capture_output=True, text=True, check=True
    )
    quoted = subprocess.run(
        [str(BASH), "-c", 'printf %q "$1"', "test", value],
        capture_output=True,
        text=True,
        check=True,
    )
    assert output.stdout == f"value={value} quoted={quoted.stdout}\n"
