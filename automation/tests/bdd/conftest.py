"""Registration and fixtures for the Gherkin suite.

``pytest-bdd`` 9 turns every step definition into a pytest fixture, so the modules
that define them have to be visible to pytest as plugins. ``pytest_plugins`` is
only accepted in a conftest at the pytest rootdir, and that rootdir is
``pyshellforge/`` -- the automation suite deliberately sits beside the automation
instead, outside it -- so this conftest imports the step modules itself and adopts
the fixtures they created. A conftest's own namespace is a plugin namespace, which
is why the adoption makes the steps visible to every scenario below it.

Only the step fixtures are adopted, by the name prefix pytest-bdd gives them: a
plain ``import *`` would also drag the helpers of each module into one namespace,
where several of them share a name.
"""

from __future__ import annotations

import importlib
import pathlib
import sys

import pytest
from pytest_bdd.steps import StepNamePrefix

#: The step modules of this suite. Adding a feature file means adding its steps
#: here as well; `python -m automation.gherkin` reports a definition no scenario
#: uses and a step no module defines.
STEP_MODULES = (
    "steps_agents",
    "steps_automation_cli",
    "steps_docs",
    "steps_features",
    "steps_forms",
    "steps_readme",
    "steps_release",
    "steps_restore",
)

BDD_DIR = pathlib.Path(__file__).resolve().parent
if str(BDD_DIR) not in sys.path:
    sys.path.insert(0, str(BDD_DIR))

_STEP_FIXTURE_PREFIX = f"{StepNamePrefix.step_def.value}_"
for _module_name in STEP_MODULES:
    _module = importlib.import_module(_module_name)
    globals().update(
        (name, value)
        for name, value in vars(_module).items()
        if name.startswith(_STEP_FIXTURE_PREFIX)
    )


@pytest.fixture
def context() -> dict[str, object]:
    """Mutable per-scenario state shared between steps."""
    return {}
