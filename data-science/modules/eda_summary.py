
"""EDA summary + late vs on-time hypothesis test example."""
from __future__ import annotations
import json
from pathlib import Path
import duckdb
import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "data-engineering" / "warehouse" / "nexus.duckdb"
OUT = Path(__file__).resolve().parents[1] / "outputs"

def run():
    OUT.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB), read_only=True)
    late = con.execute("SELECT net_sales FROM fact_orders WHERE is_late=1 AND is_revenue=1").df()["net_sales"]
    ontime = con.execute("SELECT net_sales FROM fact_orders WHERE is_on_time=1 AND is_revenue=1").df()["net_sales"]
    # Welch t-test: mean net_sales late vs on-time
    t, p = stats.ttest_ind(late, ontime, equal_var=False, nan_policy="omit")
    corr = con.execute("""
        SELECT corr(is_late::DOUBLE, days_ship_real::DOUBLE) AS corr_late_days,
               corr(is_otif::DOUBLE, line_profit::DOUBLE) AS corr_otif_profit
        FROM fact_orders WHERE is_revenue=1
    """).fetchone()
    # simple segment by ABC
    seg = con.execute("""
        SELECT p.abc_class,
               ROUND(AVG(o.is_otif)*100,2) AS otif_pct,
               ROUND(AVG(o.is_late)*100,2) AS late_pct,
               COUNT(*) AS lines
        FROM fact_orders o
        JOIN dim_product p ON o.product_key = p.product_key
        GROUP BY 1 ORDER BY 1
    """).df()
    con.close()
    report = {
        "hypothesis": "Mean net_sales differs between late and on-time revenue lines",
        "n_late": int(len(late)),
        "n_ontime": int(len(ontime)),
        "mean_late": round(float(late.mean()), 2),
        "mean_ontime": round(float(ontime.mean()), 2),
        "welch_t": round(float(t), 4),
        "p_value": float(p),
        "correlations": {"late_vs_days_ship": corr[0], "otif_vs_profit": corr[1]},
        "abc_segmentation": seg.to_dict(orient="records"),
        "note": "Illustrative stats on public extract — not a causal claim.",
    }
    (OUT / "eda_hypothesis.json").write_text(json.dumps(report, indent=2))
    return report

if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
