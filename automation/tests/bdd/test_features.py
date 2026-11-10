"""Bind every Gherkin feature file to its step definitions.

Adding a feature file means adding it here; ``python -m automation.gherkin``
reports steps that have no definition and definitions that no scenario uses.
The step modules are star-imported by the sibling ``conftest.py``, which is what
makes their fixtures visible to the scenarios below.
"""

from __future__ import annotations

from pytest_bdd import scenarios

scenarios(
    "../../features/agents_file.feature",
    "../../features/readme_generation.feature",
    "../../features/session_restore.feature",
    "../../features/docs_validation.feature",
    "../../features/feature_lint.feature",
    "../../features/issue_forms.feature",
    "../../features/release_build.feature",
    "../../features/automation_cli.feature",
)
