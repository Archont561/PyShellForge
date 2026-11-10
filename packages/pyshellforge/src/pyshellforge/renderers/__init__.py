"""Renderers and their common errors."""

from __future__ import annotations


class UnsupportedNodeError(ValueError):
    """The selected renderer cannot express a node."""

    def __init__(self, node: object, target: str) -> None:
        super().__init__(f"{type(node).__name__} is not supported by {target}")


class InterpolationError(ValueError):
    """An interpolation is malformed or refers to an undeclared variable."""
