"""Shell-neutral building blocks for a script."""

from __future__ import annotations

from dataclasses import dataclass

from .base import Node
from .nodes.echo import Echo


@dataclass(frozen=True)
class Comment(Node):
    """A comment, with no leading comment marker."""

    text: str


@dataclass(frozen=True)
class VariableAssignment(Node):
    """Assign a literal value to a shell variable."""

    name: str
    value: str


@dataclass(frozen=True)
class Command(Node):
    """A command and literal arguments, never a raw shell fragment."""

    name: str
    args: tuple[str, ...] = ()


__all__ = ["Command", "Comment", "Echo", "Node", "VariableAssignment"]
