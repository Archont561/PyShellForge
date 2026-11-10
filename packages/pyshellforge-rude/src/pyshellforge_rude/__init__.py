"""PyShellForge conventions as rules for the Rude linter.

Rude discovers the ``RULES`` list through the ``rude.plugins`` entry point, so
installing this distribution is the whole setup:

    pip install packages/pyshellforge-rude
    rude check src/
"""

from __future__ import annotations

from pyshellforge_rude.rules import LocalsAreLowerCase, ModuleGlobalsAreUpperCase

RULES = [ModuleGlobalsAreUpperCase, LocalsAreLowerCase]

__all__ = ["RULES", "LocalsAreLowerCase", "ModuleGlobalsAreUpperCase"]
