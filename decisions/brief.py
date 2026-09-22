"""Monday ops decision brief — markdown from warehouse economics + exceptions."""
from __future__ import annotations

from datetime import datetime, timezone

from decisions.economics import carrier_exceptions, value_at_stake, warehouse_exceptions
from inferential.studies import claim_summary


def build_brief() -> str:
    v = value_at_stake()
    wh = warehouse_exceptions(limit=5)
    cr = carrier_exceptions(limit=5)
    yoy = v.get("yoy_2016_2017") or {}
    lines = [
        f"# NEXUS decision brief",
        f"Generated `{datetime.now(timezone.utc).isoformat()}` from the local DuckDB extract.",
        "",
        "## Value at stake (proxies, not GAAP)",
        f"- Revenue **${v['revenue']:,.0f}**; **{v['late_revenue_share_pct']}%** of it sits on late lines (${v['late_revenue']:,.0f}).",
        f"- OTIF **{v['actual_otif_pct']}%**" + (
            f" (Wilson 95% CI {v['otif_wilson']['lo']}–{v['otif_wilson']['hi']})"
            if v.get("otif_wilson") and v["otif_wilson"].get("lo") is not None
            else ""
        ) + f" vs SAMPLE enterprise target **{v['sample_otif_target_pct']}%** (gap {v['otif_gap_pp']} pp).",
        f"- Shipment delay_cost **${v['delay_cost']:,.0f}**; expedite freight **${v['expedite_freight']:,.0f}**.",
        f"- Inventory unfilled_value (all snapshots) **${v['unfilled_value_all_snapshots']:,.0f}**.",
        f"- 180d inactivity LTV proxy **${v['churn_ltv_at_risk_proxy']:,.0f}**.",
        "",
        "## Why revenue moved (2016 → 2017)",
    ]
    if yoy:
        lines.append(
            f"- Calendar revenue ${yoy['revenue_from_m']}M → ${yoy['revenue_to_m']}M (**{yoy['delta_m']}M**). {yoy['note']}"
        )
    else:
        lines.append("- YoY pair not available.")
    lines += ["", "## Top warehouse exceptions (late-line revenue)", ""]
    for row in wh:
        lines.append(
            f"- **{row['warehouse_name']}**: late revenue ${row['late_revenue']:,.0f} · late {row['late_pct']}% · OTIF {row['otif_pct']}% → {row['action']}"
        )
    lines += ["", "## Top carriers by delay_cost", ""]
    for row in cr:
        lines.append(
            f"- **{row['carrier_name']}**: delay_cost ${row['delay_cost']:,.0f} · late {row['late_pct']}% → {row['action']}"
        )
    inferred = claim_summary()
    lines += [
        "",
        "## Inferential engineering",
        f"- {inferred['line']}",
        "- Advance-shipping contrasts are registered separately and are refused as effects.",
        "",
        "## Guardrails",
        "- Policies in `docs/knowledge/` are SAMPLE.",
        "- Late revenue ≠ lost sales. Do not quote these as recovered EBITDA.",
        "",
    ]
    return "\n".join(lines)
