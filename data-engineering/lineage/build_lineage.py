"""Emit simple column/table lineage JSON for the NEXUS warehouse."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "lineage" / "lineage.json"

def build() -> dict:
    lineage = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "nodes": [
            {"id": "src.dataco", "type": "source", "label": "DataCo Smart Supply Chain extract"},
            {"id": "src.retail_uk", "type": "source", "label": "Online Retail II (UK) extract"},
            {"id": "landing.parquet", "type": "landing"},
            {"id": "cleaned.parquet", "type": "cleaned"},
            {"id": "warehouse.duckdb", "type": "warehouse"},
            {"id": "analytics.kpi_sql", "type": "analytics"},
            {"id": "ml.demand_forecast", "type": "ml"},
            {"id": "ml.anomaly_otif", "type": "ml"},
            {"id": "ml.churn", "type": "ml"},
            {"id": "ai.investigate", "type": "ai"},
            {"id": "dashboard.powerbi", "type": "bi"},
        ],
        "edges": [
            {"from": "src.dataco", "to": "landing.parquet"},
            {"from": "src.retail_uk", "to": "landing.parquet"},
            {"from": "landing.parquet", "to": "cleaned.parquet", "transform": "flag_coerce"},
            {"from": "cleaned.parquet", "to": "warehouse.duckdb", "transform": "duckdb_load"},
            {"from": "warehouse.duckdb", "to": "analytics.kpi_sql"},
            {"from": "warehouse.duckdb", "to": "ml.demand_forecast"},
            {"from": "warehouse.duckdb", "to": "ml.anomaly_otif"},
            {"from": "warehouse.duckdb", "to": "ml.churn"},
            {"from": "warehouse.duckdb", "to": "ai.investigate"},
            {"from": "cleaned.parquet", "to": "dashboard.powerbi"},
        ],
    }
    OUT.write_text(json.dumps(lineage, indent=2))
    return lineage

if __name__ == "__main__":
    build()
    print("lineage written", OUT)
