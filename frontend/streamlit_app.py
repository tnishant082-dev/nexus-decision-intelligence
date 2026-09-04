"""NEXUS Decision Intelligence — Streamlit console."""
from __future__ import annotations
import json
import os
import sys
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
API_KEY = os.getenv("NEXUS_API_KEY", "dev-nexus-key")
HEADERS = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

st.set_page_config(page_title="NEXUS Decision Intelligence", page_icon="◆", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 1.2rem;}
div[data-testid="stMetricValue"] {font-size: 1.6rem;}
.nexus-banner {background: linear-gradient(90deg,#0B1F33,#123A56); color:#E8F1F8;
  padding:1rem 1.25rem; border-radius:12px; margin-bottom:1rem;}
.nexus-banner h1 {margin:0; font-size:1.6rem; letter-spacing:0.04em;}
.nexus-banner p {margin:0.25rem 0 0; opacity:0.85; font-size:0.95rem;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="nexus-banner">
  <h1>NEXUS Decision Intelligence Platform</h1>
  <p>Retail + supply chain · local-first · mock LLM default · DataCo + Online Retail II extracts</p>
</div>
""", unsafe_allow_html=True)

def api(method, path, **kwargs):
    url = f"{API_URL}{path}"
    try:
        r = requests.request(method, url, headers=HEADERS, timeout=60, **kwargs)
        if r.status_code == 401:
            st.error("Unauthorized — set NEXUS_API_KEY")
            return None
        return r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text
    except requests.exceptions.ConnectionError:
        return None

def local_kpis():
    """Fallback KPIs directly from DuckDB if API is down."""
    try:
        from ai.tools.sql_tool import run_sql
        return {
            "executive": (run_sql("SELECT * FROM v_exec_kpis").get("rows") or [{}])[0],
            "otif": (run_sql("SELECT * FROM v_otif_order").get("rows") or [{}])[0],
            "logistics": (run_sql("SELECT * FROM v_logistics").get("rows") or [{}])[0],
        }
    except Exception as e:
        st.warning(f"Warehouse not ready: {e}")
        return {}

tabs = st.tabs([
    "Command Center", "Analytics", "Predictions", "AI Analyst",
    "Knowledge", "Agent Workspace", "Inference Monitor", "ML Experiments",
])

# ---- Command Center ----
with tabs[0]:
    st.subheader("Executive Command Center")
    data = api("GET", "/api/v1/kpis") or local_kpis()
    if data:
        ex, ot, lg = data.get("executive", {}), data.get("otif", {}), data.get("logistics", {})
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.metric("Revenue", f"${ex.get('revenue_m', '—')}M")
        c2.metric("Profit", f"${ex.get('profit_m', '—')}M")
        c3.metric("Orders", f"{ex.get('orders', '—')}")
        c4.metric("OTIF", f"{ot.get('otif_pct', '—')}%")
        c5.metric("Perfect order", f"{ot.get('perfect_order_pct', '—')}%")
        c6.metric("Delay rate", f"{lg.get('delay_rate_pct', '—')}%")
        st.caption("Source: DuckDB warehouse over public DataCo / Online Retail II extracts in `data/`. Not a live production feed.")
        st.info("Power BI Analytics layer remains under `dashboard/` — mapped as NEXUS Executive Command Center pages (see analytics/README.md).")
    else:
        st.warning("Start API (`uvicorn backend.main:app`) or run data-engineering pipeline first.")

# ---- Analytics ----
with tabs[1]:
    st.subheader("Analytics")
    st.markdown("Run curated KPI SQL against the warehouse (read-only).")
    default_sql = "SELECT * FROM v_otif_order"
    sql = st.text_area("SQL", value=default_sql, height=120)
    if st.button("Run query", key="sql_run"):
        from ai.tools.sql_tool import run_sql
        res = run_sql(sql)
        if res.get("ok"):
            st.dataframe(pd.DataFrame(res["rows"]), use_container_width=True)
        else:
            st.error(res.get("error"))
    st.markdown("**Power BI page map** → see `analytics/README.md`")

# ---- Predictions ----
with tabs[2]:
    st.subheader("Predictions")
    st.caption("Uses registered models under `ml/registry/` when trained.")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("#### Demand forecast (category/week features)")
        cat = st.text_input("category_name", "Electronics")
        lag1 = st.number_input("lag1", value=100.0)
        if st.button("Predict demand"):
            body = {"rows": [{"category_name": cat, "lag1": lag1, "lag2": lag1 * 0.9,
                              "lag4": lag1 * 0.8, "roll4": lag1, "weekofyear": 20, "month": 5}]}
            r = api("POST", "/api/v1/ml/forecast", json=body)
            st.json(r or {"hint": "API offline — train with python -m ml.run_all"})
    with col_b:
        st.markdown("#### OTIF anomaly score")
        otif = st.slider("otif_rate", 0.0, 1.0, 0.35)
        late = st.slider("late_rate", 0.0, 1.0, 0.55)
        if st.button("Score anomaly"):
            body = {"rows": [{"otif_rate": otif, "late_rate": late, "perfect_rate": 0.2,
                              "revenue": 50000, "lines": 200}]}
            r = api("POST", "/api/v1/ml/anomaly", json=body)
            st.json(r or {"hint": "API offline"})

# ---- AI Analyst ----
with tabs[3]:
    st.subheader("AI Analyst")
    q = st.text_input("Question", "Why is OTIF low and which warehouses drive late deliveries?")
    if st.button("Investigate", type="primary"):
        with st.spinner("Running multi-agent investigate..."):
            r = api("POST", "/api/v1/investigate", json={"question": q})
            if r is None:
                from ai.agents.investigate import investigate
                r = investigate(q)
            st.markdown("#### Drivers")
            for d in r.get("drivers", []):
                st.write(f"- {d}")
            st.markdown("#### Recommendations")
            for rec in r.get("recommendations", []):
                st.write(f"- {rec}")
            st.metric("Confidence", r.get("confidence"))
            with st.expander("Evidence trail"):
                st.json(r.get("evidence"))
            with st.expander("Agent trail"):
                st.json(r.get("agent_trail"))
            st.caption(r.get("disclaimer", ""))

# ---- Knowledge ----
with tabs[4]:
    st.subheader("Knowledge (sample SOPs)")
    qk = st.text_input("Search policies", "OTIF escalation expedite")
    if st.button("Retrieve"):
        from ai.rag.retriever import retrieve
        hits = retrieve(qk)
        for h in hits:
            st.markdown(f"**{h['title']}** (`{h['doc_id']}`) · score {h['score']}")
            st.write(h["snippet"][:400] + "…")
    st.caption("Policies under docs/knowledge/ are clearly labeled SAMPLE.")

# ---- Agent Workspace ----
with tabs[5]:
    st.subheader("Agent Workspace")
    st.markdown("Orchestrator → analytics → forecast → inventory → RAG → decision")
    st.code("""POST /api/v1/investigate
{"question": "What is driving late deliveries and how should we respond?"}""", language="bash")
    if st.button("Run sample investigate"):
        from ai.agents.investigate import investigate
        st.json(investigate("What is driving late deliveries and how should we respond?"))

# ---- Inference Monitor ----
with tabs[6]:
    st.subheader("Inference Monitor")
    prompt = st.text_area("Prompt", "Summarize OTIF drivers for leadership.")
    force = st.selectbox("Force route", [None, "mock", "small", "large"])
    if st.button("Complete"):
        from inference.gateway import complete
        st.json(complete(prompt, force=force))
    from inference.gateway import stats
    st.markdown("#### Gateway stats")
    st.json(stats())
    st.caption("Hardware label is always cpu_local_mock — no fake GPUs.")

# ---- ML Experiments ----
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
    if reg.exists():
        st.markdown("#### Registry")
        for f in sorted(reg.glob("*.json")):
            st.json(json.loads(f.read_text()))
