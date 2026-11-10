"""``python -m automation.readme`` entry point."""

from __future__ import annotations

from .generate import main

if __name__ == "__main__":  # pragma: no cover - module entry point
    raise SystemExit(main())
