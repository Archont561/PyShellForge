"""``AGENTS.md`` generation and maintenance for this repository.

``python -m automation.agents --bootstrap`` creates the file with the pinned
``agents-md`` CLI; ``python -m automation.agents --check`` enforces its marker
contract offline, which is what CI runs.
"""

from __future__ import annotations

from .generate import (
    CLI_PACKAGE,
    CODES,
    PACKAGE_JSON,
    REPO_ROOT,
    SECTIONS,
    SIDECAR,
    STUB,
    TARGET,
    TITLES,
    Finding,
    begin_marker,
    bootstrap,
    check_agents,
    end_marker,
    generator_command,
    main,
    markers_in,
    pinned_version,
    section_body,
    subprocess_runner,
)

__all__ = [
    "CLI_PACKAGE",
    "CODES",
    "PACKAGE_JSON",
    "REPO_ROOT",
    "SECTIONS",
    "SIDECAR",
    "STUB",
    "TARGET",
    "TITLES",
    "Finding",
    "begin_marker",
    "bootstrap",
    "check_agents",
    "end_marker",
    "generator_command",
    "main",
    "markers_in",
    "pinned_version",
    "section_body",
    "subprocess_runner",
]
