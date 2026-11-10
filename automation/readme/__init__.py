"""README generation driven by readme-md-generator.

``python -m automation.readme`` renders ``automation/readme/README.ejs`` through the
pinned npm generator and writes the result to the repository root.
"""

from __future__ import annotations

from .generate import (
    ATTRIBUTION,
    BANNER_MARKER,
    GENERATOR_PACKAGE,
    PACKAGE_JSON,
    REPO_ROOT,
    TARGET,
    TEMPLATE,
    ReadmeResult,
    generator_command,
    inject_banner,
    main,
    pinned_version,
    render_readme,
    subprocess_runner,
    write_readme,
)

__all__ = [
    "ATTRIBUTION",
    "BANNER_MARKER",
    "GENERATOR_PACKAGE",
    "PACKAGE_JSON",
    "REPO_ROOT",
    "TARGET",
    "TEMPLATE",
    "ReadmeResult",
    "generator_command",
    "inject_banner",
    "main",
    "pinned_version",
    "render_readme",
    "subprocess_runner",
    "write_readme",
]
