"""A safe, explicit template for printing text."""

from __future__ import annotations

from ..base import Node


class Echo(Node):
    """Print a template: ``{NAME}`` expands a declared variable, ``{{`` is literal.

    ``{NAME!q}`` requests Bash's runtime shell quoting; other conversions and
    format specifications are not supported. Templates are strings, not Python
    f-strings, so Python cannot interpolate them before the renderer sees them.
    """

    def __init__(self, template: str) -> None:
        self.template = template
