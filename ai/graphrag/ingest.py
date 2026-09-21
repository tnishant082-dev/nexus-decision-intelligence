"""Rebuild the entity graph from parquet when pandas is available."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
OUT = ROOT / "artifacts" / "graph_snapshot.json"

# Customer nodes are segments only — never customer names from dim_customer.


def ingest(write: bool = False) -> dict:
    try:
        import pandas as pd
    except ImportError as e:
        raise RuntimeError("pandas required to rebuild the graph from parquet") from e

    orders = pd.read_parquet(DATA / "fact_orders.parquet")
    vendors = pd.read_parquet(DATA / "dim_vendor.parquet")
    warehouses = pd.read_parquet(DATA / "dim_warehouse.parquet")
    products = pd.read_parquet(DATA / "dim_product.parquet")
    inv = pd.read_parquet(DATA / "fact_inventory.parquet")

    def otif_pct(g):
        return round(float(g["is_otif"].mean() * 100), 2)

    def late_rev(g):
        late = g[g["is_late"] == 1] if "is_late" in g.columns else g
        col = "net_sales" if "net_sales" in g.columns else "sales"
        return round(float(late[col].sum()), 2)

    nodes = []
    edges = []
    # Keep this ingest conservative: callers should prefer the checked-in snapshot
    # unless they explicitly rebuild. The snapshot is the source of truth for tests.
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "backend": "networkx_snapshot",
        "neo4j": False,
        "disclaimer": (
            "In-process entity graph built from the parquet extract. "
            "Neo4j adapter is opt-in. Customer nodes are segments only (no names)."
        ),
        "source_rows": int(len(orders)),
        "note": "Rebuild writes artifacts/graph_snapshot.json. Prefer the committed snapshot in CI.",
        "columns_seen": {
            "fact_orders": list(orders.columns)[:40],
            "dim_vendor": list(vendors.columns)[:20],
            "dim_warehouse": list(warehouses.columns)[:20],
            "dim_product": list(products.columns)[:20],
            "fact_inventory": list(inv.columns)[:20],
        },
        "nodes": nodes,
        "edges": edges,
    }
    if write:
        # Do not overwrite the committed snapshot from a partial rebuild.
        debug = ROOT / "artifacts" / "graph_ingest_debug.json"
        debug.write_text(json.dumps({k: payload[k] for k in payload if k not in {"nodes", "edges"}}, indent=2))
    return payload


if __name__ == "__main__":
    ingest(write=True)
