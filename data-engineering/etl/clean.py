"""Clean landing parquet into typed cleaned tables (null keys, flag coercion)."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
LANDING = ROOT / "landing"
CLEANED = ROOT / "cleaned"

FLAG_COLS = ("is_canceled", "is_fraud", "is_revenue", "is_late", "is_on_time",
             "is_otif", "is_perfect_order", "is_advance", "is_in_full",
             "is_canceled_ship", "stockout_flag", "is_on_time_receipt",
             "preferred_flag", "is_active", "is_weekend", "is_holiday")

def _coerce_flags(df: pd.DataFrame) -> pd.DataFrame:
    for c in FLAG_COLS:
        if c in df.columns:
            df[c] = df[c].fillna(0).astype(int).clip(0, 1)
    return df

def clean(landing: Path = LANDING, cleaned: Path = CLEANED) -> dict:
    cleaned.mkdir(parents=True, exist_ok=True)
    report = {"cleaned_at": datetime.now(timezone.utc).isoformat(), "tables": []}
    for p in sorted(landing.glob("*.parquet")):
        df = pd.read_parquet(p)
        before = len(df)
        df = _coerce_flags(df)
        # drop fully empty rows if any
        df = df.dropna(how="all")
        out = cleaned / p.name
        df.to_parquet(out, index=False)
        report["tables"].append({
            "name": p.name, "rows_in": before, "rows_out": len(df),
            "columns": list(df.columns),
        })
    (cleaned / "clean_report.json").write_text(json.dumps(report, indent=2))
    return report

if __name__ == "__main__":
    print(json.dumps(clean(), indent=2)[:600])
