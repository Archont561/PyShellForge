"""Render the first shell-neutral nodes as Bash."""

from __future__ import annotations

import re
from collections.abc import Sequence

from ..ast import Command, Comment, Echo, Node, VariableAssignment
from . import InterpolationError, UnsupportedNodeError

IDENTIFIER = re.compile(r"[a-zA-Z_][a-zA-Z0-9_]*\Z")
SAFE_LITERAL = re.compile(r"[a-zA-Z0-9_./:@%+,=-]+\Z")
RESERVED = frozenset(
    {
        "if",
        "then",
        "else",
        "elif",
        "fi",
        "case",
        "esac",
        "for",
        "while",
        "until",
        "do",
        "done",
        "in",
        "function",
        "select",
        "time",
        "coproc",
        "!",
        "{",
        "}",
    }
)


def _quote_control(value: str) -> str:
    """Use a Bash ANSI-C string for control characters."""
    parts: list[str] = []
    for char in value:
        code = ord(char)
        if code < 32 or code == 127:
            parts.append(f"\\x{code:02x}")
        elif char in "\\'":
            parts.append("\\" + char)
        else:
            parts.append(char)
    return "$'" + "".join(parts) + "'"


def quote_literal(value: str, *, command: bool = False) -> str:
    """Quote one literal for Bash; reject NUL, which shell strings cannot carry."""
    if "\0" in value:
        raise ValueError("Bash strings cannot contain NUL")
    if (
        value
        and SAFE_LITERAL.fullmatch(value)
        and not (command and (value in RESERVED or "=" in value))
    ):
        return value
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        return _quote_control(value)
    return "'" + value.replace("'", "'\\''") + "'"


def _identifier(name: str) -> bool:
    return IDENTIFIER.fullmatch(name) is not None


def _escape_double(text: str) -> str:
    if "\0" in text or "\n" in text or "\r" in text:
        raise InterpolationError("Echo templates cannot contain NUL or line breaks")
    return "".join("\\" + char if char in '\\"$`' else char for char in text)


def _expansion(name: str, conversion: str | None, declared: set[str]) -> str:
    if not _identifier(name):
        raise InterpolationError(f"invalid variable name: {name!r}")
    if name not in declared:
        raise InterpolationError(f"undeclared variable: {name}")
    expansion = "${" + name + "}"
    if conversion is None:
        return expansion
    if conversion == "q":
        return '$(printf %q "' + expansion + '")'
    raise InterpolationError(f"unsupported conversion: !{conversion}")


def _field(field: str, declared: set[str]) -> str:
    """Expand a plain name or the supported runtime-quote conversion."""
    if ":" in field:
        raise InterpolationError("format specifications are not supported")
    name, separator, conversion = field.partition("!")
    return _expansion(name, conversion if separator else None, declared)


def _template(template: str, declared: set[str]) -> str:
    """Render a template without evaluating Python expressions or shell code."""
    pieces: list[str] = []
    index = 0
    while index < len(template):
        char = template[index]
        if char in "{}" and template[index : index + 2] == char * 2:
            pieces.append(char)
            index += 2
        elif char == "{":
            end = template.find("}", index + 1)
            if end == -1:
                raise InterpolationError("unclosed interpolation")
            pieces.append(_field(template[index + 1 : end], declared))
            index = end + 1
        elif char == "}":
            raise InterpolationError("unmatched closing brace")
        else:
            pieces.append(_escape_double(char))
            index += 1
    return '"' + "".join(pieces) + '"'


class BashRenderer:
    """Render nodes in order, tracking variables declared earlier in the script."""

    def render(self, nodes: Sequence[Node]) -> str:
        """Return a complete Bash script, terminated with a newline."""
        lines = ["#!/usr/bin/env bash"]
        declared: set[str] = set()
        for node in nodes:
            lines.extend(self._render_node(node, declared))
        return "\n".join(lines) + "\n"

    def _render_node(self, node: Node, declared: set[str]) -> list[str]:
        if isinstance(node, Comment):
            if "\0" in node.text or "\r" in node.text:
                raise ValueError("comments cannot contain NUL or carriage returns")
            lines = (line.rstrip() for line in node.text.split("\n"))
            return ["# " + line if line else "#" for line in lines]
        if isinstance(node, VariableAssignment):
            if not _identifier(node.name):
                raise ValueError(f"invalid variable name: {node.name!r}")
            declared.add(node.name)
            return [node.name + "=" + quote_literal(node.value)]
        if isinstance(node, Command):
            if not node.name:
                raise ValueError("command name must not be empty")
            return [
                " ".join(
                    [
                        quote_literal(node.name, command=True),
                        *(quote_literal(arg) for arg in node.args),
                    ]
                )
            ]
        if isinstance(node, Echo):
            return ["printf '%s\\n' " + _template(node.template, declared)]
        raise UnsupportedNodeError(node, "bash")
