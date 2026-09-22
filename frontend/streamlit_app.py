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
        if r.status_code >= 400:
            return None
        if r.headers.get("content-type", "").startswith("application/json"):
            return r.json()
        return None
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
    "Command Center", "Decision Board", "Analytics", "Predictions", "AI Analyst",
    "Knowledge", "Agent Workspace", "Inference Monitor", "ML Experiments",
    "GraphRAG", "Twin", "Copilot", "Quality", "Eval", "Inferential",
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
        vas = api("GET", "/api/v1/value-at-stake")
        if vas and vas.get("summary"):
            s = vas["summary"]
            wci = s.get("otif_wilson") or {}
            if wci.get("lo") is not None:
                st.caption(
                    f"OTIF Wilson 95% CI {wci.get('lo')}–{wci.get('hi')} "
                    f"(n={wci.get('n'):,} orders). SAMPLE target {s.get('sample_otif_target_pct')}%."
                )
            st.markdown("#### Value at stake (service-risk pool, not lost sales)")
            v1, v2, v3, v4 = st.columns(4)
            v1.metric("Late-line revenue", f"${s.get('late_revenue', 0)/1e6:.1f}M", f"{s.get('late_revenue_share_pct')}% of sales")
            v2.metric("OTIF gap vs SAMPLE 92%", f"{s.get('otif_gap_pp')} pp")
            v3.metric("Delay cost", f"${s.get('delay_cost', 0)/1e3:.0f}k")
            v4.metric("Expedite freight", f"${s.get('expedite_freight', 0)/1e3:.0f}k")
            yoy = s.get("yoy_2016_2017") or {}
            if yoy:
                st.caption(f"2016→2017 revenue ${yoy.get('revenue_from_m')}M → ${yoy.get('revenue_to_m')}M ({yoy.get('delta_m')}M). Late $ is exposure, not recovered EBITDA.")
        growth = data.get("growth") or []
        if growth:
            gdf = pd.DataFrame(growth)
            st.plotly_chart(px.bar(gdf, x="year", y="revenue_m", title="Revenue by calendar year (extract)"), use_container_width=True)
            st.download_button("Export growth CSV", gdf.to_csv(index=False), "growth.csv", "text/csv")
        st.caption("Source: DuckDB over public extracts. Inventory $ across snapshots is not a single-day balance sheet.")
    else:
        st.warning("Start API (`uvicorn backend.main:app`) or run the data-engineering pipeline first.")

with tabs[1]:
    st.subheader("Decision Board")
    st.caption("Rank exceptions by dollars, run linear what-ifs, write a Monday brief, accept/reject actions.")
    from decisions.economics import carrier_exceptions, warehouse_exceptions
    from decisions.scenarios import close_late_gap, cut_expedite, list_warehouses
    from decisions.brief import build_brief
    from decisions import ledger

    wh = pd.DataFrame(warehouse_exceptions())
    if not wh.empty:
        st.plotly_chart(px.bar(wh, x="warehouse_name", y="late_revenue", title="Late-line revenue by warehouse"), use_container_width=True)
        st.dataframe(wh, use_container_width=True)
        st.caption(
            "Late-line revenue is service-risk exposure on the 2015-01-01 → 2018-01-31 extract, not lost sales. "
            "OTIF Wilson 95% intervals are on order grain. Late % remains line-weighted."
        )
        st.download_button("Export exceptions CSV", wh.to_csv(index=False), "exceptions.csv", "text/csv")
    names = list_warehouses()
    colx, coly = st.columns(2)
    with colx:
        wh_name = st.selectbox("Warehouse (or All)", ["NETWORK"] + names)
        close = st.slider("Close this share of late-line $", 0.05, 1.0, 0.25)
        if st.button("Run late-gap scenario"):
            scope = None if wh_name == "NETWORK" else wh_name
            st.json(close_late_gap(warehouse_name=scope, close_pct=close))
    with coly:
        cut = st.slider("Cut expedite freight share", 0.05, 1.0, 0.30)
        if st.button("Run expedite scenario"):
            st.json(cut_expedite(cut_pct=cut))
    brief = build_brief()
    st.markdown("#### Monday ops brief")
    st.markdown(brief)
    st.download_button("Download brief.md", brief, "nexus-decision-brief.md", "text/markdown")
    st.markdown("#### Action ledger")
    title = st.text_input("Action title", "Attack highest-$ late warehouse")
    owner = st.text_input("Owner", "Warehouse ops")
    if st.button("Propose action"):
        top = warehouse_exceptions(limit=1)
        dollars = float(top[0]["late_revenue"]) if top else None
        ledger.add(title, "Sized from late-line revenue pool", dollars, owner)
        st.success("Added")
    items = ledger.list_items()
    if items:
        st.dataframe(pd.DataFrame(items), use_container_width=True)
        iid = st.selectbox("Update id", [i["id"] for i in items])
        stt = st.selectbox("Status", ["proposed", "accepted", "rejected", "done"])
        if st.button("Update status"):
            ledger.set_status(iid, stt)

with tabs[2]:
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

with tabs[3]:
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

with tabs[4]:
    st.subheader("AI Analyst")
    q = st.text_input("Question", "Why is OTIF low and which warehouses drive late deliveries?")
    human = st.checkbox("Human review mode (hold recommendations)")
    if st.button("Investigate", type="primary"):
        with st.spinner("Running multi-agent investigate..."):
            r = api("POST", "/api/v1/investigate", json={"question": q, "human_review": human})
            if r is None:
                from ai.agents.investigate import investigate

                r = investigate(q, human_review=human)
            if r.get("pending_review"):
                st.warning("These actions are held until an operator approves them.")
            cards = r.get("action_cards") or []
            st.markdown("#### What to do")
            if cards:
                for card in cards:
                    st.markdown(f"**{card.get('action')}**")
                    st.caption(
                        f"{card.get('metric')} — {card.get('means')} "
                        f"Does not mean: {card.get('does_not_mean')} "
                        f"Extract {card.get('extract_window')}."
                    )
            else:
                for rec in r.get("recommendations", []):
                    st.write(f"- {rec}")
            st.caption(
                f"Evidence completeness {r.get('confidence')} — how much SQL, policy, and model evidence came back. "
                "Not the probability that the action is right."
            )
            drivers = r.get("drivers") or []
            if drivers:
                with st.expander("What the extract shows"):
                    for d in drivers:
                        st.write(f"- {d}")
            if r.get("value_at_stake"):
                with st.expander("Underlying figures"):
                    st.json(r["value_at_stake"])
            st.caption("Citations: " + ", ".join(r.get("citations") or []))
            with st.expander("Evidence trail"):
                st.json(r.get("evidence"))
            with st.expander("Agent trail"):
                st.json(r.get("agent_trail"))
            st.download_button("Export investigate JSON", json.dumps(r, indent=2), "investigate.json")
            st.caption(r.get("disclaimer", ""))

with tabs[5]:
    st.subheader("Knowledge Center")
    qk = st.text_input("Search policies", "OTIF escalation expedite")
    if st.button("Retrieve"):
        from ai.rag.retriever import retrieve

        for h in retrieve(qk):
            st.markdown(f"**{h['title']}** (`{h.get('citation') or h['doc_id']}`) · score {h['score']}")
            st.write(h["snippet"][:400] + "…")
    st.caption("Policies under docs/knowledge/ are SAMPLE.")

with tabs[6]:
    st.subheader("Agent Workspace")
    st.markdown("Orchestrator → analytics/SQL → forecast → inventory → risk → RAG → decision")
    if st.button("Run sample investigate"):
        from ai.agents.investigate import investigate

        payload = investigate("What is driving late deliveries and how should we respond?")
        st.json(payload)
        st.download_button("Export", json.dumps(payload, indent=2), "agent.json")

with tabs[7]:
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

with tabs[8]:
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

with tabs[9]:
    st.subheader("GraphRAG")
    st.caption("In-process snapshot. Neo4j is idle unless NEO4J_URI is set.")
    from ai.graphrag.retrieve import graph_retrieve
    from ai.graphrag.neo4j_adapter import status as neo4j_status
    from ai.graphrag.graph import load_graph

    g = load_graph()
    st.json({"counts": g.get("counts"), "neo4j": neo4j_status()})
    gq = st.text_input("Graph question", "Which suppliers are indirectly responsible for OTIF failures?")
    if st.button("Retrieve graph"):
        st.json(graph_retrieve(gq))

with tabs[10]:
    st.subheader("Linear SAMPLE twin")
    st.caption("Not a digital twin of OMS/WMS physics.")
    from simulation.engine import simulate, describe_shock

    kind = st.selectbox("Shock", ["inventory", "supplier_delay", "demand", "price", "promotion"])
    pct = st.slider("pct", -30, 40, 20)
    days = st.slider("days", 1, 14, 5)
    if st.button("Run shock"):
        shock = {"kind": kind}
        if kind in {"inventory", "demand", "price"}:
            shock["pct"] = pct
        if kind == "supplier_delay":
            shock["days"] = days
        r = simulate(shock)
        st.write(describe_shock(shock))
        st.json(r)

with tabs[11]:
    st.subheader("Monday brief")
    from copilot.brief import monday_brief_markdown

    st.markdown(monday_brief_markdown())

with tabs[12]:
    st.subheader("Data quality")
    from quality.command import score as qscore

    st.json(qscore())

with tabs[13]:
    st.subheader("Agent evaluation")
    from evaluation.runner import run_evaluation

    if st.button("Run evaluation"):
        st.json(run_evaluation())

with tabs[14]:
    st.subheader("Inferential engineering")
    st.caption(
        "Estimand, adjustment, interval, sensitivity, verdict. "
        "This tab is not the LLM Inference Monitor."
    )
    from inferential.studies import run_board

    board = run_board()
    for card in board.get("studies") or []:
        st.markdown(f"#### {card.get('title') or card.get('study_id')}")
        if not card.get("ok"):
            st.warning(card.get("error") or "Study did not run.")
            continue
        estimate = card["estimate"]
        decision = card["decision"]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Verdict", decision["verdict"])
        c2.metric("Adjusted gap", f"{estimate.get('adjusted_risk_difference_pp')} pp")
        c3.metric("95% CI low", f"{estimate.get('ci_low_pp')} pp")
        c4.metric("95% CI high", f"{estimate.get('ci_high_pp')} pp")
        st.write(decision.get("action"))
        st.caption(decision.get("reason"))
        with st.expander("Claim card"):
            st.json(card)

