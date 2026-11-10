"""Script container and renderer protocol."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from ..ast import Node
from ..renderers.bash import BashRenderer


class Renderer(Protocol):
    """A renderer translates a sequence of nodes into a script."""

    def render(self, nodes: Sequence[Node]) -> str:
        """Render nodes to text."""
        ...


class ShellScript:
    """Collect nodes and render them through a supplied renderer."""

    def __init__(self, renderer: Renderer | None = None) -> None:
        self.renderer: Renderer = renderer if renderer is not None else BashRenderer()
        self._nodes: list[Node] = []

    def add(self, *nodes: Node) -> ShellScript:
        """Append nodes in order and return this script for chaining."""
        if not all(isinstance(node, Node) for node in nodes):
            raise TypeError("all items must be shell nodes")
        self._nodes.extend(nodes)
        return self

    def render(self) -> str:
        """Render an independent snapshot of the nodes."""
        return self.renderer.render(tuple(self._nodes))
