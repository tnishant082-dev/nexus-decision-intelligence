"""Graph search / retrieval over supplier–warehouse–segment joins."""
from __future__ import annotations

from ai.graphrag.graph import in_edges, load_graph, node_by_id, nodes_of, out_edges


def suppliers_responsible_for_otif(limit: int = 8, payload: dict | None = None) -> list[dict]:
    payload = payload or load_graph()
    rows = []
    for s in nodes_of(payload, "Supplier"):
        warehouses = [e for e in out_edges(payload, s["id"]) if e.get("rel") == "SUPPLIES_WAREHOUSE"]
        warehouses.sort(key=lambda e: e.get("late_revenue") or 0, reverse=True)
        rows.append(
            {
                "supplier": s,
                "late_revenue": float(s.get("late_revenue") or 0),
                "otif_pct": float(s.get("otif_pct") or 0),
                "warehouses": warehouses,
            }
        )
    rows.sort(key=lambda r: r["late_revenue"], reverse=True)
    return rows[:limit]


def customers_affected_by_supplier(supplier_id: str, payload: dict | None = None) -> dict:
    payload = payload or load_graph()
    supplier = node_by_id(payload, supplier_id)
    warehouses = [
        e["target"]
        for e in out_edges(payload, supplier_id)
        if e.get("rel") == "SUPPLIES_WAREHOUSE"
    ]
    customers = []
    for c in nodes_of(payload, "Customer"):
        links = [
            e
            for e in out_edges(payload, c["id"])
            if e.get("rel") == "ORDERS_FROM" and e.get("target") in warehouses
        ]
        if not links:
            continue
        customers.append(
            {
                "customer": c,
                "late_revenue": sum(e.get("late_revenue") or 0 for e in links),
                "orders": sum(e.get("orders") or 0 for e in links),
                "via_warehouses": [e["target"] for e in links],
            }
        )
    customers.sort(key=lambda r: r["late_revenue"], reverse=True)
    return {"supplier": supplier, "customers": customers}


def warehouse_supplier_deps(payload: dict | None = None) -> list[dict]:
    payload = payload or load_graph()
    out = []
    for w in nodes_of(payload, "Warehouse"):
        inbound = [e for e in in_edges(payload, w["id"]) if e.get("rel") == "SUPPLIES_WAREHOUSE"]
        inbound.sort(key=lambda e: e.get("late_revenue") or 0, reverse=True)
        out.append(
            {
                "warehouse": w,
                "suppliers": [
                    {"edge": e, "supplier": node_by_id(payload, e["source"])} for e in inbound
                ],
            }
        )
    return out


def graph_retrieve(question: str, payload: dict | None = None) -> dict:
    payload = payload or load_graph()
    q = question.lower()
    note = payload.get("disclaimer") or ""
    if "supplier" in q and any(k in q for k in ("otif", "late", "fail")):
        rows = suppliers_responsible_for_otif(5, payload)
        return {
            "intent": "suppliers_otif",
            "note": note,
            "hits": [
                {
                    "title": r["supplier"]["name"],
                    "path": [r["supplier"]["id"], *[e["target"] for e in r["warehouses"][:2]]],
                    "score": r["late_revenue"],
                    "detail": (
                        f"{r['supplier']['name']} carries ${r['late_revenue']/1e6:.2f}M late-line "
                        f"revenue at OTIF {r['otif_pct']}%. Indirect OTIF pressure via warehouse "
                        "supply edges, not a causal claim."
                    ),
                    "citations": [f"graph:supplier-rank#{i}", "SAMPLE OTIF policy"],
                }
                for i, r in enumerate(rows)
            ],
        }
    if "customer" in q and ("disrupt" in q or "supplier" in q):
        top = suppliers_responsible_for_otif(1, payload)[0]
        aff = customers_affected_by_supplier(top["supplier"]["id"], payload)
        return {
            "intent": "customers_supplier_disruption",
            "note": note,
            "hits": [
                {
                    "title": c["customer"]["name"],
                    "path": [top["supplier"]["id"], *c["via_warehouses"], c["customer"]["id"]],
                    "score": c["late_revenue"],
                    "detail": (
                        f"Segment {c['customer']['name']}: {c['orders']:,} orders at warehouses "
                        f"supplied by {top['supplier']['name']}. Customers are segments (no names)."
                    ),
                    "citations": [f"graph:supplier:{top['supplier']['name']}"],
                }
                for c in aff["customers"]
            ],
        }
    if "depend" in q or ("warehouse" in q and "supplier" in q):
        return {
            "intent": "warehouse_supplier_deps",
            "note": note,
            "hits": [
                {
                    "title": w["warehouse"]["name"],
                    "path": [w["warehouse"]["id"], *[s["supplier"]["id"] for s in w["suppliers"][:3] if s.get("supplier")]],
                    "score": float(w["warehouse"].get("late_revenue") or 0),
                    "detail": (
                        f"{w['warehouse']['name']} is supplied by {len(w['suppliers'])} vendors."
                    ),
                    "citations": ["graph:SUPPLIES_WAREHOUSE"],
                }
                for w in warehouse_supplier_deps(payload)
            ],
        }
    ranked = suppliers_responsible_for_otif(3, payload)
    return {
        "intent": "generic",
        "note": note,
        "hits": [
            {
                "title": r["supplier"]["name"],
                "path": [r["supplier"]["id"]],
                "score": r["late_revenue"],
                "detail": f"Fallback rank by late-line $. {r['supplier']['name']}: ${r['late_revenue']/1e6:.2f}M.",
                "citations": ["graph:generic"],
            }
            for r in ranked
        ],
    }
