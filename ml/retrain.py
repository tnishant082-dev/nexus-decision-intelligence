"""Retrain entrypoint for local/CI (not a hosted scheduler)."""
from __future__ import annotations

from ml.run_all import main

if __name__ == "__main__":
    raise SystemExit(main())
