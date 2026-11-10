"""PyShellForge — the package surface.

The package exposes the script container, initial nodes and Bash renderer.

The version has a single source of truth, ``[project].version`` in
``pyproject.toml``. Reading it at import time keeps the value honest — there is no
second copy to forget — and it needs care in one respect: a wheel does not ship
``pyproject.toml``. The order below therefore degrades instead of failing, so that
``import pyshellforge`` works in a source checkout, from an installed
distribution and from a vendored package:

1. ``pyproject.toml`` found by walking up from this file (source checkout);
2. installed distribution metadata (wheel, sdist, editable install);
3. :data:`FALLBACK_VERSION`, which exists so that an import never raises.

Usage::

    >>> import pyshellforge
    >>> pyshellforge.VERSION
    '0.1.0'
"""

from __future__ import annotations

import re
import tomllib
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from .ast import Command, Comment, Echo, Node, VariableAssignment
from .core import ShellScript
from .renderers import InterpolationError, UnsupportedNodeError
from .renderers.bash import BashRenderer

__all__ = [
    "VERSION",
    "BashRenderer",
    "Command",
    "Comment",
    "Echo",
    "InterpolationError",
    "Node",
    "ShellScript",
    "UnsupportedNodeError",
    "VariableAssignment",
]

#: Distribution name used for metadata lookups.
DIST_NAME = "pyshellforge"

#: File searched for when no metadata is installed.
PYPROJECT_NAME = "pyproject.toml"

#: Last resort, so that a vendored package still imports.
FALLBACK_VERSION = "0.1.0"

#: Conservative check so a malformed file cannot leak garbage into a version string.
VERSION_RE = re.compile(r"^\d+(\.\d+)*([.-]?[0-9A-Za-z.]+)?$")


def find_pyproject(start: str | Path | None = None) -> Path | None:
    """Return the ``pyproject.toml`` above ``start`` (default: this file), or ``None``."""
    location = Path(start) if start is not None else Path(__file__)
    try:
        location = location.resolve()
    except OSError:  # pragma: no cover - broken symlink
        return None
    directory = location if location.is_dir() else location.parent
    for candidate_dir in (directory, *directory.parents):
        candidate = candidate_dir / PYPROJECT_NAME
        if candidate.is_file():
            return candidate
    return None


def read_version(pyproject: str | Path) -> str | None:
    """Return ``[project].version`` from ``pyproject.toml``, or ``None`` when unusable."""
    path = Path(pyproject)
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError):
        return None
    project = data.get("project")
    if not isinstance(project, dict):
        return None
    value = project.get("version")
    if not isinstance(value, str) or not VERSION_RE.match(value.strip()):
        return None
    return value.strip()


def installed_version(dist: str = DIST_NAME) -> str | None:
    """Return the version recorded in installed distribution metadata, or ``None``."""
    try:
        return version(dist)
    except PackageNotFoundError:
        return None
    except Exception:  # pragma: no cover - defensive: corrupt metadata
        return None


def resolve_version() -> str:
    """Resolve the project version in the documented order."""
    pyproject = find_pyproject()
    if pyproject is not None:
        resolved = read_version(pyproject)
        if resolved:
            return resolved
    return installed_version() or FALLBACK_VERSION


#: The project version, read from ``pyproject.toml`` (see :func:`resolve_version`).
VERSION = resolve_version()
