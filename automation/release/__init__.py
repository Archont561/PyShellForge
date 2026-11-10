"""Build the release distributions, guarded by the tag and the version.

``python -m automation.release`` is the local half of
``.github/workflows/release.yml``: it refuses a tag that disagrees with
``[project].version``, then builds and checks the sdist and the wheel.
"""

from __future__ import annotations

from .build import (
    CI_REF_ENV,
    DIST_NAME,
    PYPROJECT_NAME,
    REPO_ROOT,
    Plan,
    ReleaseError,
    Request,
    Runner,
    build_distributions,
    check_distributions,
    clean_distributions,
    main,
    read_package_version,
    release,
    subprocess_runner,
    tag_of,
    verify_tag,
)

__all__ = [
    "CI_REF_ENV",
    "DIST_NAME",
    "PYPROJECT_NAME",
    "REPO_ROOT",
    "Plan",
    "ReleaseError",
    "Request",
    "Runner",
    "build_distributions",
    "check_distributions",
    "clean_distributions",
    "main",
    "read_package_version",
    "release",
    "subprocess_runner",
    "tag_of",
    "verify_tag",
]
