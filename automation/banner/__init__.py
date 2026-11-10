"""FIGlet art for the README banner, rendered instead of pasted.

``automation.readme`` asks this module for the wordmark, and
``python -m automation.banner`` draws any other text the same way.
"""

from __future__ import annotations

from .render import (
    DEFAULT_COMMENT_PREFIX,
    DEFAULT_FONT,
    DEFAULT_WIDTH,
    WORDMARK,
    get_banner_width,
    list_fonts,
    main,
    render_banner,
    render_comment_banner,
)

__all__ = [
    "DEFAULT_COMMENT_PREFIX",
    "DEFAULT_FONT",
    "DEFAULT_WIDTH",
    "WORDMARK",
    "get_banner_width",
    "list_fonts",
    "main",
    "render_banner",
    "render_comment_banner",
]
