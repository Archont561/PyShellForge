"""Tests for ``automation.banner``.

The module has one job that matters: the banner in the README is rendered
from the font data, not pasted, so the committed page and pyfiglet must agree.
These tests pin that agreement, the shape of the art, and the CLI contract.
"""

from __future__ import annotations

import re

import pytest

from automation.banner import render
from automation.banner.render import (
    DEFAULT_COMMENT_PREFIX,
    DEFAULT_FONT,
    WORDMARK,
    get_banner_width,
    list_fonts,
    main,
    render_banner,
    render_comment_banner,
)
from automation.readme import generate


# -- the wordmark -------------------------------------------------------------
def test_the_wordmark_is_six_rows_wide_enough_to_stay_on_one_line() -> None:
    art = render_banner(WORDMARK)
    rows = art.splitlines()
    assert len(rows) == 6, "the README banner is six rows"
    assert max(len(row) for row in rows) == 99


def test_the_art_carries_no_invisible_padding() -> None:
    art = render_banner(WORDMARK)
    assert not art.endswith("\n"), "the caller places the art, so it ends without a newline"
    assert all(row == row.rstrip() for row in art.splitlines())


def test_the_committed_readme_carries_the_rendered_art() -> None:
    """The banner is a generated artefact: a font change has to reach the page."""
    page = (generate.REPO_ROOT / "README.md").read_text(encoding="utf-8")
    inside_pre = re.search(r"<pre[^>]*>\n(?P<art>.*?)</pre>", page, re.DOTALL)
    assert inside_pre, "the README should open with the banner inside a <pre> block"
    assert inside_pre.group("art") == render_banner(WORDMARK)


def test_the_wordmark_has_no_lower_case_letters() -> None:
    """The banner spells the product name, and the name is upper case."""
    assert WORDMARK == "PYSHELLFORGE"


# -- arguments ----------------------------------------------------------------
@pytest.mark.parametrize("text", ["", "   ", "\n"])
def test_blank_text_is_rejected(text: str) -> None:
    with pytest.raises(ValueError, match="cannot be blank"):
        render_banner(text)


def test_an_unknown_font_is_reported_with_the_way_out() -> None:
    with pytest.raises(ValueError, match="--list-fonts"):
        render_banner(WORDMARK, font="no-such-font")


def test_the_font_list_is_sorted_and_holds_the_default() -> None:
    fonts = list_fonts()
    assert fonts == tuple(sorted(fonts))
    assert DEFAULT_FONT in fonts


def test_a_narrower_width_folds_the_wordmark() -> None:
    assert len(render_banner(WORDMARK, width=40).splitlines()) > 6


def test_the_reported_width_matches_the_widest_row() -> None:
    art = render_banner(WORDMARK)
    assert get_banner_width(WORDMARK) == max(len(row) for row in art.splitlines())


def test_the_default_font_is_the_one_the_readme_uses() -> None:
    assert DEFAULT_FONT == "ansi_shadow"


# -- the comment block --------------------------------------------------------
def test_a_comment_banner_prefixes_every_row() -> None:
    art = render_banner(WORDMARK)
    commented = render_comment_banner(WORDMARK)
    assert commented.splitlines() == [f"{DEFAULT_COMMENT_PREFIX}{row}" for row in art.splitlines()]


def test_a_comment_banner_takes_its_own_prefix() -> None:
    commented = render_comment_banner("Hi", prefix="//")
    assert commented.splitlines()
    assert all(row.startswith("//") for row in commented.splitlines())


# -- the CLI ------------------------------------------------------------------
def test_the_cli_defaults_to_the_wordmark(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([]) == 0
    assert capsys.readouterr().out.rstrip("\n") == render_banner(WORDMARK)


def test_the_cli_draws_the_text_it_is_given(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["Hi"]) == 0
    assert capsys.readouterr().out.rstrip("\n") == render_banner("Hi")


def test_the_cli_passes_the_font_through(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["Hi", "--font", "standard"]) == 0
    assert capsys.readouterr().out.rstrip("\n") == render_banner("Hi", font="standard")


def test_the_cli_passes_the_width_through(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([WORDMARK, "--width", "40"]) == 0
    assert capsys.readouterr().out.rstrip("\n") == render_banner(WORDMARK, width=40)


def test_the_cli_can_comment_the_art(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["Hi", "--comment"]) == 0
    assert capsys.readouterr().out.rstrip("\n") == render_comment_banner("Hi")


def test_the_cli_takes_a_comment_prefix(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["Hi", "--comment", "//"]) == 0
    assert capsys.readouterr().out.rstrip("\n") == render_comment_banner("Hi", prefix="//")


def test_the_cli_lists_the_fonts(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--list-fonts"]) == 0
    printed = capsys.readouterr().out.splitlines()
    assert tuple(printed) == list_fonts()


def test_the_cli_reports_a_bad_font_as_a_usage_error(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--font", "no-such-font"]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "unknown figlet font" in captured.err


def test_the_cli_reports_blank_text_as_a_usage_error(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["   "]) == 2
    assert "cannot be blank" in capsys.readouterr().err


def test_the_module_reexports_what_the_cli_needs() -> None:
    assert render.main is main
    assert render.WORDMARK == WORDMARK
