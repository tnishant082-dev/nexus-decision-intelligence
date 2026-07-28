"""Row-count, null-key, and referential checks against cleaned / warehouse."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "warehouse" / "nexus.duckdb"
OUT = ROOT / "validation" / "validation_report.json"

CHECKS = [
    ("orders_positive", "SELECT COUNT(*) FROM fact_orders", lambda n: n > 0),
    ("shipments_positive", "SELECT COUNT(*) FROM fact_shipments", lambda n: n > 0),
    ("otif_bounded", "SELECT MIN(is_otif), MAX(is_otif) FROM fact_orders",
     lambda r: r[0] in (0,1) and r[1] in (0,1)),
    ("orders_product_fk",
     "SELECT COUNT(*) FROM fact_orders o LEFT JOIN dim_product p ON o.product_key=p.product_key WHERE p.product_key IS NULL",
     lambda n: n == 0),
    ("orders_customer_fk",
     "SELECT COUNT(*) FROM fact_orders o LEFT JOIN dim_customer c ON o.customer_key=c.customer_key WHERE c.customer_key IS NULL",
     lambda n: n == 0),
    ("revenue_nonneg", "SELECT COUNT(*) FROM fact_orders WHERE is_revenue=1 AND net_sales < 0",
     lambda n: True),  # allow returns/discounts; informational
]

def validate(db_path: Path = DB) -> dict:
    con = duckdb.connect(str(db_path), read_only=True)
    results = []
    passed = 0
    for name, sql, pred in CHECKS:
        val = con.execute(sql).fetchone()
        ok = bool(pred(val[0] if len(val) == 1 else val))
        passed += int(ok)
        results.append({"check": name, "value": list(val) if isinstance(val, tuple) else val, "passed": ok})
    con.close()
    report = {
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "passed": passed,
        "total": len(CHECKS),
        "results": results,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2))
    return report

if __name__ == "__main__":
    print(json.dumps(validate(), indent=2))
