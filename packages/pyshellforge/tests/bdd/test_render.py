"""Bind the product scenarios to their step definitions."""

from pytest_bdd import scenarios

from .steps_render import *  # noqa: F403

scenarios("../../features/bash_rendering.feature")
