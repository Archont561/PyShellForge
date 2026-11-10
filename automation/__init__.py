"""Repository automation for PyShellForge.

Everything under ``automation/`` is tooling that operates on the repository itself
(README generation, documentation validation, Gherkin linting, release builds, CI
change detection). It is deliberately separate from the ``pyshellforge`` package:
the product never imports these modules, and they are not shipped in the wheel.

The modules are ordinary Python and know nothing about doit: every one exposes a
``main(argv)`` entry point, is typed, and is exercised by tests in
``automation/tests/`` plus the Gherkin scenarios in ``automation/features/``.
``dodo.py`` at the repository root registers them as tasks, so both of these work:

    python -m automation.docs          # run one module directly
    pixi run automation check-docs     # run it through the task graph
"""

from __future__ import annotations

__all__ = ["__version__"]

#: Automation follows the package version so diagnostics can be tied to a release.
__version__ = "0.1.0"
