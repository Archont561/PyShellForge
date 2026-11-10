"""Restore the developer environment: Pixi, the solved environment and the hooks.

``python -m automation.restore`` runs before the first ``pixi run`` of a session and
is the only repository script that does not assume Pixi exists.
"""

from __future__ import annotations

from .generate import (
    HOOK_MARKER,
    INSTALLER_URL,
    PIXI_HOME,
    PIXI_VERSION,
    REPO_ROOT,
    State,
    Tooling,
    binary_path,
    environment_ready,
    hooks_installed,
    inspect,
    install_environment,
    install_hooks,
    install_pixi,
    installer_env,
    is_git_repository,
    main,
    make_executable,
    pixi_env,
    restore,
    subprocess_runner,
    url_fetcher,
    which_pixi,
)

__all__ = [
    "HOOK_MARKER",
    "INSTALLER_URL",
    "PIXI_HOME",
    "PIXI_VERSION",
    "REPO_ROOT",
    "State",
    "Tooling",
    "binary_path",
    "environment_ready",
    "hooks_installed",
    "inspect",
    "install_environment",
    "install_hooks",
    "install_pixi",
    "installer_env",
    "is_git_repository",
    "main",
    "make_executable",
    "pixi_env",
    "restore",
    "subprocess_runner",
    "url_fetcher",
    "which_pixi",
]
