"""Data catalog: table descriptions, grain, PII notes, owners."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "warehouse" / "nexus.duckdb"
OUT = ROOT / "catalog" / "catalog.json"
OUT_MD = ROOT / "catalog" / "catalog.md"

DESCRIPTIONS = {
    "fact_orders": {"grain": "order line", "domain": "oms", "pii": False,
                    "desc": "Order lines with revenue, OTIF, late, perfect-order flags"},
    "fact_shipments": {"grain": "shipment", "domain": "tms", "pii": False,
                       "desc": "Shipments with freight, delay, fill (in-full), CO2, OTIF"},
    "fact_inventory": {"grain": "product x warehouse x date", "domain": "wms", "pii": False,
                       "desc": "Inventory snapshots with on-hand, backorder, stockout"},
    "fact_procurement": {"grain": "PO line", "domain": "procurement", "pii": False,
                         "desc": "Purchase orders with SLA receipt flags"},
    "fact_returns": {"grain": "return line", "domain": "oms", "pii": False,
                     "desc": "Returns / cancellations linked to orders"},
    "dim_customer": {"grain": "customer", "domain": "crm", "pii": True,
                     "desc": "Customers (names present in extract — treat as demo PII)"},
    "dim_product": {"grain": "product", "domain": "mdm", "pii": False,
                    "desc": "Products with category, ABC class, list price"},
    "dim_vendor": {"grain": "vendor", "domain": "procurement", "pii": False,
                   "desc": "Vendors with preferred flag and risk tier"},
    "dim_warehouse": {"grain": "warehouse", "domain": "wms", "pii": False,
                      "desc": "Warehouses by market"},
    "dim_date": {"grain": "day", "domain": "calendar", "pii": False,
                 "desc": "Calendar incl. DataCo partial-year flags"},
}


def build(db_path: Path = DB) -> dict:
    con = duckdb.connect(str(db_path), read_only=True)
    tables = []
    views = []
    for row in con.execute("SHOW TABLES").fetchall():
        name = row[0]
        n = con.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
        cols = [c[0] for c in con.execute(f"DESCRIBE {name}").fetchall()]
        meta = DESCRIPTIONS.get(name, {"grain": "unknown", "domain": "other", "pii": False, "desc": name})
        entry = {"name": name, "rows": n, "columns": cols, **meta}
        if name.startswith("v_"):
            views.append(entry)
        else:
            tables.append(entry)
    con.close()
    catalog = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "owner": "Nishant Tyagi",
        "platform": "NEXUS Decision Intelligence",
        "tables": tables,
        "views": views,
    }
    OUT.write_text(json.dumps(catalog, indent=2))
    lines = [
        "# NEXUS data catalog",
        "",
        f"Generated `{catalog['generated_at']}` from DuckDB.",
        "",
        "## Tables",
        "",
        "| table | rows | grain | domain | PII |",
        "|---|---:|---|---|---|",
    ]
    for t in tables:
        lines.append(f"| `{t['name']}` | {t['rows']} | {t['grain']} | {t['domain']} | {t['pii']} |")
    lines += ["", "## Views", "", "| view | rows (scan) |", "|---|---:|"]
    for v in views:
        lines.append(f"| `{v['name']}` | {v['rows']} |")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return catalog


if __name__ == "__main__":
    c = build()
    print(f"catalog: {len(c['tables'])} tables, {len(c.get('views', []))} views")
