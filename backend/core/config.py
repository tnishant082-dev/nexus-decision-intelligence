from __future__ import annotations

import hmac
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
API_KEY = os.getenv("NEXUS_API_KEY", "dev-nexus-key")
RATE_LIMIT = os.getenv("NEXUS_RATE_LIMIT", "60/minute")
DB_PATH = ROOT / "data-engineering" / "warehouse" / "nexus.duckdb"
CORS_ORIGINS = [o.strip() for o in os.getenv("NEXUS_CORS_ORIGINS", "http://127.0.0.1:8501,http://localhost:8501").split(",") if o.strip()]
AUDIT_ENABLED = os.getenv("NEXUS_AUDIT", "1") == "1"


def api_key_ok(provided: str | None) -> bool:
    if not provided:
        return False
    return hmac.compare_digest(provided.encode("utf-8"), API_KEY.encode("utf-8"))
