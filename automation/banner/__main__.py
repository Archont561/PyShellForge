"""``python -m automation.banner`` entry point."""

from __future__ import annotations

from .render import main

if __name__ == "__main__":  # pragma: no cover - module entry point
    raise SystemExit(main())
