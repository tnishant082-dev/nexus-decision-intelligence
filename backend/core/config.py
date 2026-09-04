
from __future__ import annotations
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
API_KEY = os.getenv("NEXUS_API_KEY", "dev-nexus-key")
RATE_LIMIT = os.getenv("NEXUS_RATE_LIMIT", "60/minute")
DB_PATH = ROOT / "data-engineering" / "warehouse" / "nexus.duckdb"
