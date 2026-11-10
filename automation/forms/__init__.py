"""Validation for the GitHub Issue Forms in ``.github/ISSUE_TEMPLATE/``.

``python -m automation.forms`` checks the templates offline, which is what CI can
do; ``gh form preview`` renders them in a browser, which needs the GitHub CLI.
"""

from __future__ import annotations

from .check import (
    CODES,
    CONFIG_NAME,
    ELEMENT_TYPES,
    ID_TYPES,
    LABELLED_TYPES,
    REPO_ROOT,
    TEMPLATE_DIR,
    VALIDATION_KEYS,
    Finding,
    check_config,
    check_forms,
    check_template,
    form_files,
    main,
    template_files,
)

__all__ = [
    "CODES",
    "CONFIG_NAME",
    "ELEMENT_TYPES",
    "ID_TYPES",
    "LABELLED_TYPES",
    "REPO_ROOT",
    "TEMPLATE_DIR",
    "VALIDATION_KEYS",
    "Finding",
    "check_config",
    "check_forms",
    "check_template",
    "form_files",
    "main",
    "template_files",
]
