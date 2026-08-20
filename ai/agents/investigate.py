"""Multi-agent investigate flow: orchestrator → analytics → forecast → inventory → RAG → decision."""
from __future__ import annotations
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from ai.rag.retriever import retrieve
from ai.tools.sql_tool import run_sql, KPI_SNIPPETS

REGISTRY = Path(__file__).resolve().parents[2] / "ml" / "registry"

def _load_model_ids() -> list[str]:
    ids = []
    if REGISTRY.exists():
        for p in REGISTRY.glob("*.json"):
            try:
                ids.append(json.loads(p.read_text()).get("model_id", p.stem))
            except Exception:
                ids.append(p.stem)
    return ids

def _pick_snippets(question: str) -> list[str]:
    q = question.lower()
    keys = []
    if any(w in q for w in ("otif", "on-time", "on time", "perfect order", "service")):
        keys += ["otif", "late_by_warehouse", "late_by_carrier"]
    if any(w in q for w in ("freight", "carrier", "delay", "late", "logistics", "expedite")):
        keys += ["logistics", "late_by_carrier"]
    if any(w in q for w in ("inventory", "stock", "stockout", "coverage", "working capital")):
        keys += ["inventory_coverage"]
    if any(w in q for w in ("revenue", "profit", "executive", "kpi", "sales")):
        keys += ["exec_kpis", "category_revenue"]
    if any(w in q for w in ("forecast", "demand", "category")):
        keys += ["category_revenue"]
    if not keys:
        keys = ["exec_kpis", "otif", "logistics"]
    # unique preserve order
    seen = set()
    out = []
    for k in keys:
        if k not in seen:
            seen.add(k)
            out.append(k)
    return out[:4]

def investigate(question: str) -> dict:
    """Killer endpoint logic — returns drivers, recommendations, evidence, confidence."""
    trail = []
    evidence = {"sql": [], "models": [], "documents": []}

    # 1) Orchestrator
    trail.append({"agent": "orchestrator", "action": "plan", "detail": "Route to analytics, forecast context, inventory, RAG, decision"})

    # 2) Analytics agent
    snippets = _pick_snippets(question)
    drivers = []
    for key in snippets:
        sql = KPI_SNIPPETS[key].strip()
        result = run_sql(sql, limit=20)
        trail.append({"agent": "analytics", "action": f"run:{key}", "ok": result.get("ok")})
        if result.get("ok"):
            evidence["sql"].append({"name": key, "sql": sql, "sample_rows": result["rows"][:5]})
            # extract simple driver text
            rows = result["rows"]
            if key == "otif" and rows:
                drivers.append(f"Network OTIF {rows[0].get('otif_pct')}%; perfect-order {rows[0].get('perfect_order_pct')}%")
            elif key == "logistics" and rows:
                drivers.append(f"Delay rate {rows[0].get('delay_rate_pct')}%; freight ${rows[0].get('freight_m')}M; CO2 {rows[0].get('co2_tonnes')} t")
            elif key == "late_by_warehouse" and rows:
                top = rows[0]
                drivers.append(f"Highest late % warehouse: {top.get('warehouse_name')} ({top.get('late_pct')}%)")
            elif key == "late_by_carrier" and rows:
                top = rows[0]
                drivers.append(f"Highest late % carrier: {top.get('carrier_name')} ({top.get('late_pct')}%)")
            elif key == "exec_kpis" and rows:
                drivers.append(f"Revenue ${rows[0].get('revenue_m')}M; profit ${rows[0].get('profit_m')}M; orders {rows[0].get('orders')}")
            elif key == "inventory_coverage" and rows:
                drivers.append(f"Inventory stockout rate {rows[0].get('stockout_pct')}% across snapshots")
            elif key == "category_revenue" and rows:
                top = rows[0]
                drivers.append(f"Top category by revenue: {top.get('category_name')} (${top.get('revenue_m')}M, OTIF {top.get('otif_pct')}%)")

    # 3) Forecast agent (reference model registry — no silent hallucination of accuracy)
    model_ids = _load_model_ids()
    trail.append({"agent": "forecast", "action": "registry_lookup", "models": model_ids})
    for mid in model_ids:
        evidence["models"].append({"model_id": mid})
        p = REGISTRY / f"{mid}.json"
        if p.exists():
            meta = json.loads(p.read_text())
            evidence["models"][-1]["stage"] = meta.get("stage")
            evidence["models"][-1]["metrics"] = meta.get("metrics")

    # 4) Inventory agent — already covered via SQL; add note
    trail.append({"agent": "inventory", "action": "coverage_check", "detail": "Used inventory_coverage / warehouse late mix"})

    # 5) RAG agent
    docs = retrieve(question, top_k=3)
    trail.append({"agent": "rag", "action": "retrieve", "hits": len(docs)})
    evidence["documents"] = docs

    # 6) Decision agent — mock LLM synthesis (honest)
    recommendations = []
    q = question.lower()
    if any(w in q for w in ("otif", "late", "delay", "service")):
        recommendations.append("Split late vs short-ship: prioritize carrier/mode actions where late % is highest.")
        recommendations.append("Align expedite policy — elevated delay often coincides with reactive air/expedite spend.")
    if any(w in q for w in ("inventory", "stock", "working capital")):
        recommendations.append("Review weeks-of-supply on A-class SKUs; long coverage with weak OTIF is a cash/service tradeoff.")
    if any(w in q for w in ("vendor", "procurement", "sla")):
        recommendations.append("Check preferred-vendor mix and on-time receipt SLA for vendors feeding late warehouses.")
    if not recommendations:
        recommendations.append("Start from Executive KPIs, then drill OTIF → warehouse → carrier; cite policy thresholds from knowledge base.")
    if docs:
        recommendations.append(f"Apply guidance from '{docs[0]['title']}' (sample policy) when prioritizing escalations.")

    # Confidence: based on evidence completeness (not fake accuracy)
    conf = 0.35
    conf += 0.15 * min(len(evidence["sql"]), 3)
    conf += 0.1 * min(len(docs), 2)
    conf += 0.1 if model_ids else 0
    conf = round(min(conf, 0.9), 2)

    return {
        "question": question,
        "drivers": drivers,
        "recommendations": recommendations,
        "evidence": evidence,
        "agent_trail": trail,
        "confidence": conf,
        "llm_mode": "mock",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "disclaimer": "Local NEXUS demo. Metrics from DuckDB warehouse over public extracts; policies are SAMPLE docs; LLM responses are template/mock unless a provider key is configured.",
    }
