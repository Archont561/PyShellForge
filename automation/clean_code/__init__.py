"""Clean Code linting with ``rude`` and ``rude-clean-code``.

``python -m automation.clean_code`` is the gate: it runs the CC rules over the
repository's Python and exits non-zero when one of them reports.
"""

from __future__ import annotations

from .check import (
    CONFIG,
    REPO_ROOT,
    SOURCES,
    Finding,
    check_repository,
    main,
    parse_findings,
    rude_command,
    subprocess_runner,
)

__all__ = [
    "CONFIG",
    "REPO_ROOT",
    "SOURCES",
    "Finding",
    "check_repository",
    "main",
    "parse_findings",
    "rude_command",
    "subprocess_runner",
]
