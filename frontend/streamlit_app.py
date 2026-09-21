"""NEXUS Decision Intelligence — Streamlit console."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
API_KEY = os.getenv("NEXUS_API_KEY", "dev-nexus-key")
HEADERS = {"X-API-Key": API_KEY, "Content-Type": "application/json", "X-Nexus-Role": "analyst"}

st.set_page_config(page_title="NEXUS Decision Intelligence", page_icon="◆", layout="wide")
st.markdown(
    """
<style>
.block-container {padding-top: 1.2rem;}
div[data-testid="stMetricValue"] {font-size: 1.55rem;}
.nexus-banner {background: linear-gradient(90deg,#0B1F33,#123A56); color:#E8F1F8;
  padding:1rem 1.25rem; border-radius:12px; margin-bottom:1rem;}
.nexus-banner h1 {margin:0; font-size:1.55rem; letter-spacing:0.04em;}
.nexus-banner p {margin:0.25rem 0 0; opacity:0.85; font-size:0.95rem;}
</style>
""",
    unsafe_allow_html=True,
)
st.markdown(
    """
<div class="nexus-banner">
  <h1>NEXUS Decision Intelligence Platform</h1>
  <p>Retail + supply chain · local-first · mock LLM default · DataCo + Online Retail II extracts</p>
</div>
""",
    unsafe_allow_html=True,
)


def api(method, path, **kwargs):
    url = f"{API_URL}{path}"
    try:
        r = requests.request(method, url, headers=HEADERS, timeout=60, **kwargs)
        if r.status_code == 401:
            st.error("Unauthorized — set NEXUS_API_KEY")
            return None
        if r.headers.get("content-type", "").startswith("application/json"):
            return r.json()
        return r.text
    except requests.exceptions.ConnectionError:
        return None


def local_kpis():
    try:
        from ai.tools.sql_tool import run_sql

        def first(sql):
            r = run_sql(sql)
            return (r.get("rows") or [{}])[0] if r.get("ok") else {}

        return {
            "executive": first("SELECT * FROM v_exec_kpis"),
            "otif": first("SELECT * FROM v_otif_order"),
            "fill": first("SELECT * FROM v_fill_rate"),
            "logistics": first("SELECT * FROM v_logistics"),
            "inventory": first("SELECT * FROM v_inventory_kpis"),
            "customer": first("SELECT * FROM v_customer_kpis"),
            "growth": run_sql("SELECT * FROM v_finance_growth").get("rows") or [],
        }
    except Exception as e:
        st.warning(f"Warehouse not ready: {e}")
        return {}


def sql_df(sql: str) -> pd.DataFrame:
    from ai.tools.sql_tool import run_sql

    res = run_sql(sql, limit=200)
    if res.get("ok"):
        return pd.DataFrame(res["rows"])
    st.error(res.get("error"))
    return pd.DataFrame()


tabs = st.tabs([
    "Command Center", "Analytics", "Predictions", "AI Analyst",
    "Knowledge", "Agent Workspace", "Inference Monitor", "ML Experiments",
])

with tabs[0]:
    st.subheader("Executive Command Center")
    data = api("GET", "/api/v1/kpis") or local_kpis()
    if data:
        ex, ot, lg = data.get("executive", {}), data.get("otif", {}), data.get("logistics", {})
        fill, inv, cust = data.get("fill", {}), data.get("inventory", {}), data.get("customer", {})
        c = st.columns(6)
        c[0].metric("Revenue", f"${ex.get('revenue_m', '—')}M")
        c[1].metric("Profit", f"${ex.get('profit_m', '—')}M")
        c[2].metric("Margin", f"{ex.get('margin_pct', '—')}%")
        c[3].metric("OTIF", f"{ot.get('otif_pct', '—')}%")
        c[4].metric("Fill rate", f"{fill.get('fill_rate_pct', '—')}%")
        c[5].metric("Perfect order", f"{ot.get('perfect_order_pct', '—')}%")
        c2 = st.columns(6)
        c2[0].metric("Delay rate", f"{lg.get('delay_rate_pct', '—')}%")
        c2[1].metric("Stockout", f"{inv.get('stockout_pct', '—')}%")
        c2[2].metric("Coverage", f"{inv.get('coverage_ratio', '—')}")
        c2[3].metric("Turns proxy", f"{inv.get('turns_proxy', '—')}")
        c2[4].metric("Retain 90d", f"{cust.get('retained_90d_pct', '—')}%")
        c2[5].metric("Churn proxy", f"{cust.get('churn_proxy_180d_pct', '—')}%")
        growth = data.get("growth") or []
        if growth:
            gdf = pd.DataFrame(growth)
            st.plotly_chart(px.bar(gdf, x="year", y="revenue_m", title="Revenue by calendar year (extract)"), use_container_width=True)
            st.download_button("Export growth CSV", gdf.to_csv(index=False), "growth.csv", "text/csv")
        st.caption("Source: DuckDB over public extracts. Inventory $ across snapshots is not a single-day balance sheet.")
    else:
        st.warning("Start API (`uvicorn backend.main:app`) or run the data-engineering pipeline first.")

with tabs[1]:
    st.subheader("Analytics")
    drill = st.selectbox("Drill-down", ["OTIF by warehouse", "Late by carrier", "Stockout by product", "Custom SQL"])
    queries = {
        "OTIF by warehouse": """
            SELECT w.warehouse_name, ROUND(AVG(o.is_late)*100,2) AS late_pct,
                   ROUND(AVG(o.is_otif)*100,2) AS otif_pct, COUNT(*) AS lines
            FROM fact_orders o JOIN dim_warehouse w ON o.warehouse_key = w.warehouse_key
            GROUP BY 1 ORDER BY late_pct DESC
        """,
        "Late by carrier": """
            SELECT c.carrier_name, ROUND(AVG(s.is_late)*100,2) AS late_pct, COUNT(*) AS shipments
            FROM fact_shipments s JOIN dim_carrier c ON s.carrier_key = c.carrier_key
            GROUP BY 1 ORDER BY late_pct DESC
        """,
        "Stockout by product": "SELECT * FROM v_stockout_risk LIMIT 30",
        "Custom SQL": "SELECT * FROM v_otif_order",
    }
    sql = st.text_area("SQL", value=queries[drill].strip(), height=140)
    if st.button("Run query", key="sql_run"):
        df = sql_df(sql)
        if not df.empty:
            st.dataframe(df, use_container_width=True)
            st.download_button("Export CSV", df.to_csv(index=False), "query.csv", "text/csv")
            num = df.select_dtypes(include="number")
            if len(df.columns) >= 2 and not num.empty:
                st.plotly_chart(px.bar(df.head(15), x=df.columns[0], y=num.columns[0]), use_container_width=True)

with tabs[2]:
    st.subheader("Predictions")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.markdown("#### Demand forecast")
        cat = st.text_input("category_name", "Electronics")
        lag1 = st.number_input("lag1", value=100.0)
        if st.button("Predict demand"):
            body = {"rows": [{"category_name": cat, "lag1": lag1, "lag2": lag1 * 0.9,
                              "lag4": lag1 * 0.8, "roll4": lag1, "weekofyear": 20, "month": 5}]}
            st.json(api("POST", "/api/v1/ml/forecast", json=body) or {"hint": "train with python -m ml.run_all"})
    with col_b:
        st.markdown("#### OTIF anomaly")
        otif = st.slider("otif_rate", 0.0, 1.0, 0.35)
        late = st.slider("late_rate", 0.0, 1.0, 0.55)
        if st.button("Score anomaly"):
            body = {"rows": [{"otif_rate": otif, "late_rate": late, "perfect_rate": 0.2, "revenue": 50000, "lines": 200}]}
            st.json(api("POST", "/api/v1/ml/anomaly", json=body) or {"hint": "API offline"})
    with col_c:
        st.markdown("#### Churn / stockout")
        if st.button("Sample churn row"):
            st.json(api("POST", "/api/v1/ml/churn", json={"rows": [{
                "frequency": 3, "monetary": 400, "tenure_days": 200, "avg_otif": 0.4, "avg_late": 0.5
            }]}) or {"hint": "train models"})
        if st.button("Sample stockout row"):
            st.json(api("POST", "/api/v1/ml/stockout", json={"rows": [{
                "avg_on_hand": 10, "avg_demand": 40, "avg_unfilled": 5, "avg_backorder": 2,
                "avg_safety": 8, "coverage": 0.25, "abc_code": 0
            }]}) or {"hint": "train models"})

with tabs[3]:
    st.subheader("AI Analyst")
    q = st.text_input("Question", "Why is OTIF low and which warehouses drive late deliveries?")
    human = st.checkbox("Human review mode (hold recommendations)")
    if st.button("Investigate", type="primary"):
        with st.spinner("Running multi-agent investigate..."):
            r = api("POST", "/api/v1/investigate", json={"question": q, "human_review": human})
            if r is None:
                from ai.agents.investigate import investigate

                r = investigate(q, human_review=human)
            st.markdown("#### Drivers")
            for d in r.get("drivers", []):
                st.write(f"- {d}")
            st.markdown("#### Recommendations")
            for rec in r.get("recommendations", []):
                st.write(f"- {rec}")
            st.metric("Confidence", r.get("confidence"))
            st.caption("Citations: " + ", ".join(r.get("citations") or []) )
            with st.expander("Evidence trail"):
                st.json(r.get("evidence"))
            with st.expander("Agent trail"):
                st.json(r.get("agent_trail"))
            st.download_button("Export investigate JSON", json.dumps(r, indent=2), "investigate.json")
            st.caption(r.get("disclaimer", ""))

with tabs[4]:
    st.subheader("Knowledge Center")
    qk = st.text_input("Search policies", "OTIF escalation expedite")
    if st.button("Retrieve"):
        from ai.rag.retriever import retrieve

        for h in retrieve(qk):
            st.markdown(f"**{h['title']}** (`{h.get('citation') or h['doc_id']}`) · score {h['score']}")
            st.write(h["snippet"][:400] + "…")
    st.caption("Policies under docs/knowledge/ are SAMPLE.")

with tabs[5]:
    st.subheader("Agent Workspace")
    st.markdown("Orchestrator → analytics/SQL → forecast → inventory → risk → RAG → decision")
    if st.button("Run sample investigate"):
        from ai.agents.investigate import investigate

        payload = investigate("What is driving late deliveries and how should we respond?")
        st.json(payload)
        st.download_button("Export", json.dumps(payload, indent=2), "agent.json")

with tabs[6]:
    st.subheader("Inference Monitor")
    prompt = st.text_area("Prompt", "Summarize OTIF drivers for leadership.")
    force = st.selectbox("Force route", [None, "mock", "small", "large", "openai", "groq", "ollama", "vllm", "llamacpp"])
    if st.button("Complete"):
        from inference.gateway import complete

        st.json(complete(prompt, force=force))
    from inference.gateway import stats

    s = stats()
    st.markdown("#### Gateway stats")
    st.json(s)
    by = pd.DataFrame(s.get("by_route") or [])
    if not by.empty and "avg_latency_ms" in by.columns:
        st.plotly_chart(px.bar(by, x="route", y="avg_latency_ms", title="Avg latency by route (local log)"), use_container_width=True)
    st.caption("Mock default. Live providers only if their env vars are set. No GPU claims.")

with tabs[7]:
    st.subheader("ML Experiments")
    exp = ROOT / "ml" / "experiments"
    reg = ROOT / "ml" / "registry"
    if exp.exists():
        files = sorted(exp.glob("*.json"))
        st.write(f"{len(files)} experiment files")
        for f in files[-10:]:
            st.markdown(f"`{f.name}`")
            st.json(json.loads(f.read_text()))
    if (ROOT / "ml" / "drift" / "last_drift.json").exists():
        st.markdown("#### Drift")
        st.json(json.loads((ROOT / "ml" / "drift" / "last_drift.json").read_text()))
    if reg.exists():
        st.markdown("#### Registry")
        for f in sorted(reg.glob("*.json")):
            st.json(json.loads(f.read_text()))
