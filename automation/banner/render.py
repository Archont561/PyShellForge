"""FIGlet art for the README banner, and for any other wordmark.

The banner at the top of ``README.md`` is not pasted by hand. The
template carries a marker, ``automation.readme`` replaces it with
:func:`render_banner` of :data:`WORDMARK`, and the freshness check fails when
the committed page and the font disagree. The same function draws any text:

    python -m automation.banner                          # the README wordmark
    python -m automation.banner "Deploy" --font slant     # another font
    python -m automation.banner Deploy --comment "# "     # a Bash header
    python -m automation.banner --list-fonts

pyfiglet is a development dependency: it sits in the ``dev`` and ``docs`` extras
and in the Pixi environment. The product does not import it and no wheel ships
it.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from pyfiglet import Figlet, FigletFont, FontNotFound

#: Font the README wordmark is drawn in. pyfiglet bundles the font data, so the
#: same 571 fonts exist wherever pyfiglet is installed.
DEFAULT_FONT = "ansi_shadow"

#: The text the README banner spells: the project name, upper case.
WORDMARK = "PYSHELLFORGE"

#: Wrap width handed to pyfiglet. Its own default, 80 columns, folds the 99
#: column wordmark onto two rows, so the banner asks for room.
DEFAULT_WIDTH = 200

#: Comment prefix a Bash header uses.
DEFAULT_COMMENT_PREFIX = "# "


def render_banner(text: str, *, font: str = DEFAULT_FONT, width: int = DEFAULT_WIDTH) -> str:
    """Render ``text`` as FIGlet art.

    Figure space inside the art is invisible padding, so trailing whitespace is
    stripped from every row and blank rows at the end are dropped: the result can
    sit inside a ``<pre>`` block or a comment without carrying it around.

    Args:
        text: the text to draw.
        font: a bundled font name, as :func:`list_fonts` reports them.
        width: the wrap width handed to pyfiglet.

    Returns:
        The art, rows separated by newlines, with no trailing newline.

    Raises:
        ValueError: if ``text`` is blank or ``font`` is not a bundled font.
    """
    if not text.strip():
        msg = "banner text cannot be blank"
        raise ValueError(msg)
    try:
        figure = Figlet(font=font, width=width)
    except FontNotFound as error:
        msg = f"unknown figlet font {font!r}; see `python -m automation.banner --list-fonts`"
        raise ValueError(msg) from error

    rows = [line.rstrip() for line in figure.renderText(text).strip("\n").splitlines()]
    while rows and not rows[-1]:
        rows.pop()
    return "\n".join(rows)


def list_fonts() -> tuple[str, ...]:
    """Return every font pyfiglet bundles, sorted by name."""
    return tuple(sorted(FigletFont.getFonts()))


def get_banner_width(text: str, *, font: str = DEFAULT_FONT, width: int = DEFAULT_WIDTH) -> int:
    """Return the column count of the widest row :func:`render_banner` produces.

    Args:
        text: the text to draw.
        font: a bundled font name.
        width: the wrap width handed to pyfiglet.

    Returns:
        The width in columns, as an integer.

    Raises:
        ValueError: if ``text`` is blank or ``font`` is not a bundled font.
    """
    return max(len(line) for line in render_banner(text, font=font, width=width).splitlines())


def render_comment_banner(
    text: str,
    *,
    prefix: str = DEFAULT_COMMENT_PREFIX,
    font: str = DEFAULT_FONT,
    width: int = DEFAULT_WIDTH,
) -> str:
    """Render the art as a comment block, one prefix per row.

    This is the shape a shell script header takes: the art stays inert because
    the shell reads every row as a comment.

    Args:
        text: the text to draw.
        prefix: what starts each row, ``"# "`` by default.
        font: a bundled font name.
        width: the wrap width handed to pyfiglet.

    Returns:
        The prefixed art, rows separated by newlines, with no trailing newline.

    Raises:
        ValueError: if ``text`` is blank or ``font`` is not a bundled font.
    """
    art = render_banner(text, font=font, width=width)
    return "\n".join(f"{prefix}{line}" for line in art.splitlines())


def _build_parser() -> argparse.ArgumentParser:
    """Return the argument parser behind ``python -m automation.banner``."""
    parser = argparse.ArgumentParser(
        prog="python -m automation.banner",
        description="Render text as FIGlet art. The README banner uses this module.",
    )
    parser.add_argument(
        "text",
        nargs="?",
        default=WORDMARK,
        help=f"the text to draw (default: {WORDMARK})",
    )
    parser.add_argument(
        "--font",
        default=DEFAULT_FONT,
        help=f"a bundled font (default: {DEFAULT_FONT})",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=DEFAULT_WIDTH,
        help=f"the wrap width handed to pyfiglet (default: {DEFAULT_WIDTH})",
    )
    parser.add_argument(
        "--comment",
        nargs="?",
        const=DEFAULT_COMMENT_PREFIX,
        default=None,
        metavar="PREFIX",
        help=f"prefix every row, so the art can sit in a script header (default: {DEFAULT_COMMENT_PREFIX!r})",
    )
    parser.add_argument(
        "--list-fonts",
        action="store_true",
        help="print every bundled font name and exit",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point: print the art, list the fonts, or report a bad argument.

    Returns:
        0 when the art or the font list was printed, 2 when the text or the font
        was rejected.
    """
    args = _build_parser().parse_args(argv)

    if args.list_fonts:
        for name in list_fonts():
            print(name)
        return 0

    try:
        art = (
            render_banner(args.text, font=args.font, width=args.width)
            if args.comment is None
            else render_comment_banner(
                args.text, prefix=args.comment, font=args.font, width=args.width
            )
        )
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    print(art)
    return 0
