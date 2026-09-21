"""Named agent nodes used by the investigate graph."""
from __future__ import annotations

import json
from pathlib import Path

from ai.rag.retriever import retrieve
from ai.tools.sql_tool import KPI_SNIPPETS, run_sql

REGISTRY = Path(__file__).resolve().parents[2] / "ml" / "registry"


def pick_snippets(question: str) -> list[str]:
    q = question.lower()
    keys = []
    if any(w in q for w in ("otif", "on-time", "on time", "perfect order", "service")):
        keys += ["otif", "late_by_warehouse", "late_by_carrier"]
    if any(w in q for w in ("freight", "carrier", "delay", "late", "logistics", "expedite")):
        keys += ["logistics", "late_by_carrier"]
    if any(w in q for w in ("inventory", "stock", "stockout", "coverage", "working capital")):
        keys += ["inventory_coverage"]
    if any(w in q for w in ("revenue", "profit", "executive", "kpi", "sales", "margin", "growth", "decline", "stake", "dollar", "impact")):
        keys += ["exec_kpis", "category_revenue", "late_revenue"]
    if any(w in q for w in ("forecast", "demand", "category")):
        keys += ["category_revenue"]
    if any(w in q for w in ("churn", "customer", "retention", "ltv")):
        keys += ["customer_kpis"]
    if any(w in q for w in ("fill", "in-full", "in full")):
        keys += ["fill_rate"]
    if not keys:
        keys = ["exec_kpis", "otif", "logistics"]
    seen: set[str] = set()
    out = []
    for k in keys:
        if k in KPI_SNIPPETS and k not in seen:
            seen.add(k)
            out.append(k)
    return out[:4]


def analytics_agent(state: dict) -> dict:
    trail = list(state.get("trail") or [])
    drivers = list(state.get("drivers") or [])
    sql_results = list(state.get("sql_results") or [])
    snippets = pick_snippets(state["question"])
    errors = list(state.get("errors") or [])
    for key in snippets:
        sql = KPI_SNIPPETS[key].strip()
        result = run_sql(sql, limit=20)
        trail.append({"agent": "analytics", "action": f"run:{key}", "ok": result.get("ok")})
        if not result.get("ok"):
            errors.append(str(result.get("error")))
            continue
        sql_results.append({"name": key, "sql": sql, "sample_rows": result["rows"][:5]})
        rows = result["rows"]
        if key == "otif" and rows:
            drivers.append(f"Network OTIF {rows[0].get('otif_pct')}%; perfect-order {rows[0].get('perfect_order_pct')}%")
        elif key == "logistics" and rows:
            drivers.append(
                f"Delay rate {rows[0].get('delay_rate_pct')}%; freight ${rows[0].get('freight_m')}M; CO2 {rows[0].get('co2_tonnes')} t"
            )
        elif key == "late_by_warehouse" and rows:
            top = rows[0]
            drivers.append(f"Highest late % warehouse: {top.get('warehouse_name')} ({top.get('late_pct')}%)")
        elif key == "late_by_carrier" and rows:
            top = rows[0]
            drivers.append(f"Highest late % carrier: {top.get('carrier_name')} ({top.get('late_pct')}%)")
        elif key == "exec_kpis" and rows:
            drivers.append(
                f"Revenue ${rows[0].get('revenue_m')}M; profit ${rows[0].get('profit_m')}M; orders {rows[0].get('orders')}"
            )
        elif key == "inventory_coverage" and rows:
            drivers.append(f"Inventory stockout rate {rows[0].get('stockout_pct')}% across snapshots")
        elif key == "category_revenue" and rows:
            top = rows[0]
            drivers.append(
                f"Top category by revenue: {top.get('category_name')} (${top.get('revenue_m')}M, OTIF {top.get('otif_pct')}%)"
            )
        elif key == "fill_rate" and rows:
            drivers.append(f"Shipment fill (in-full) {rows[0].get('fill_rate_pct')}%")
        elif key == "late_revenue" and rows:
            drivers.append(
                f"Late-line revenue ${rows[0].get('late_revenue_m')}M ({rows[0].get('late_share_pct')}% of revenue) — service-risk pool, not proven lost sales"
            )
        elif key == "customer_kpis" and rows:
            drivers.append(
                f"Customers {rows[0].get('customers')}; 180d churn proxy {rows[0].get('churn_proxy_180d_pct')}%; avg LTV ${rows[0].get('avg_ltv')}"
            )
    trail.append({"agent": "sql", "action": "curated_snippets", "count": len(sql_results)})
    return {**state, "snippets": snippets, "sql_results": sql_results, "drivers": drivers, "trail": trail, "errors": errors}


def forecast_agent(state: dict) -> dict:
    trail = list(state.get("trail") or [])
    models = []
    if REGISTRY.exists():
        for p in REGISTRY.glob("*.json"):
            try:
                meta = json.loads(p.read_text())
            except Exception:
                meta = {"model_id": p.stem}
            models.append({
                "model_id": meta.get("model_id", p.stem),
                "stage": meta.get("stage"),
                "metrics": meta.get("metrics"),
            })
    trail.append({"agent": "forecast", "action": "registry_lookup", "models": [m["model_id"] for m in models]})
    return {**state, "models": models, "trail": trail}


def inventory_agent(state: dict) -> dict:
    trail = list(state.get("trail") or [])
    notes = []
    result = run_sql("SELECT * FROM v_inventory_kpis", limit=5)
    if result.get("ok") and result["rows"]:
        row = result["rows"][0]
        notes.append(
            f"Turns proxy {row.get('turns_proxy')}; coverage ratio {row.get('coverage_ratio')}; stockout {row.get('stockout_pct')}%"
        )
        evidence = list(state.get("sql_results") or [])
        evidence.append({"name": "inventory_kpis", "sql": "SELECT * FROM v_inventory_kpis", "sample_rows": result["rows"][:5]})
        state = {**state, "sql_results": evidence}
    trail.append({"agent": "inventory", "action": "coverage_check", "ok": result.get("ok")})
    return {**state, "inventory_notes": notes, "trail": trail}


def risk_agent(state: dict) -> dict:
    trail = list(state.get("trail") or [])
    notes = []
    q = state["question"].lower()
    if any(w in q for w in ("churn", "customer", "retention")):
        r = run_sql("SELECT * FROM v_customer_kpis", limit=5)
        if r.get("ok") and r["rows"]:
            notes.append(
                f"90d retained {r['rows'][0].get('retained_90d_pct')}%; 180d churn proxy {r['rows'][0].get('churn_proxy_180d_pct')}%; avg LTV ${r['rows'][0].get('avg_ltv')}"
            )
    if any(w in q for w in ("stockout", "stock", "inventory", "risk")):
        r = run_sql("SELECT * FROM v_stockout_risk LIMIT 5", limit=5)
        if r.get("ok") and r["rows"]:
            top = r["rows"][0]
            notes.append(f"Highest snapshot stockout product: {top.get('product_name')} ({top.get('stockout_pct')}%)")
    trail.append({"agent": "risk", "action": "customer_inventory_risk", "notes": len(notes)})
    return {**state, "risk_notes": notes, "trail": trail}


def rag_agent(state: dict) -> dict:
    trail = list(state.get("trail") or [])
    docs = retrieve(state["question"], top_k=3)
    trail.append({"agent": "rag", "action": "retrieve", "hits": len(docs)})
    return {**state, "documents": docs, "trail": trail}


def decision_agent(state: dict) -> dict:
    trail = list(state.get("trail") or [])
    q = state["question"].lower()
    recs = []
    if any(w in q for w in ("otif", "late", "delay", "service", "impact", "stake")):
        recs.append("Size the late-line revenue pool first, then pick the warehouse/carrier with the largest $ — not the highest late % alone.")
        recs.append("Split late vs short-ship: prioritize carrier/mode actions where delay_cost is highest.")
    if any(w in q for w in ("freight", "expedite")):
        recs.append("Expedite freight is a small $ pool vs late revenue; cutting it blindly can worsen OTIF.")
    if any(w in q for w in ("inventory", "stock", "working capital")):
        recs.append("Review weeks-of-supply on A-class SKUs; long coverage with weak OTIF is a cash/service tradeoff.")
    if any(w in q for w in ("vendor", "procurement", "sla")):
        recs.append("Check preferred-vendor mix and on-time receipt SLA for vendors feeding late warehouses.")
    if any(w in q for w in ("churn", "customer", "retention")):
        recs.append("Treat 180-day inactivity as a proxy, not contracted churn; prioritize high-LTV lapsed accounts.")
    if any(w in q for w in ("revenue", "profit", "margin", "growth")):
        recs.append("Read annual growth from v_finance_growth with partial-year caveat before calling a decline structural.")
    if not recs:
        recs.append("Start from Executive KPIs, then drill OTIF → warehouse → carrier; cite policy thresholds from knowledge base.")
    docs = state.get("documents") or []
    if docs:
        recs.append(f"Apply guidance from '{docs[0].get('title')}' ({docs[0].get('doc_id')}) — SAMPLE policy.")
    for n in (state.get("inventory_notes") or []) + (state.get("risk_notes") or []):
        recs.append(n)
    pending = bool(state.get("human_review"))
    trail.append({"agent": "decision", "action": "synthesize", "pending_review": pending})
    return {**state, "recommendations": recs, "pending_review": pending, "trail": trail}
