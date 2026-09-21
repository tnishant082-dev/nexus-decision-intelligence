"""Monday executive brief from extract KPIs + GraphRAG ranks + SAMPLE shocks."""
from __future__ import annotations

from datetime import datetime, timezone

from ai.graphrag.retrieve import suppliers_responsible_for_otif
from simulation.engine import simulate


def monday_brief_markdown() -> str:
    top = suppliers_responsible_for_otif(3)
    inv = simulate({"kind": "inventory", "pct": 20})
    delay = simulate({"kind": "supplier_delay", "days": 5})
    lines = [
        "# NEXUS Monday executive brief",
        f"Extract window 2015-01-01 → 2018-01-31. Generated {datetime.now(timezone.utc).isoformat()}.",
        "",
        "## Revenue",
        "- **$31.64M** revenue, **$3.81M** profit, margin **12.03%**.",
        "- 2016→2017: $10.6M → $10.14M (**-0.46M**). 2018 is a partial month and is excluded from this YoY pair.",
        "",
        "## Forecast / service",
        "- OTIF **40.83%** (Wilson 95% CI 40.46–41.21, n=65,752) vs SAMPLE **92%** (gap 51.17 pp).",
        "- Demand forecast v1 holdout: WAPE 16.82%, MAE 18.63 vs lag-1 naive 21.56 (13.6% lift). Not a live forecast refresh.",
        "",
        "## Inventory risks",
        "- Snapshot stockout **0.03%**, coverage ratio **43.48**, on-hand $ (all snapshots) **$3879.95M**.",
        f"- Linear SAMPLE shock: inventory +20% → OTIF {inv['projected']['otif_pct']}% (Δ {inv['deltas']['otif_pct']} pp).",
        "",
        "## Supplier risks",
    ]
    for s in top:
        lines.append(
            f"- **{s['supplier']['name']}**: late-line ${s['late_revenue']/1e6:.2f}M · OTIF {s['otif_pct']}% · risk {s['supplier'].get('risk_tier')}."
        )
    lines += [
        f"- Linear SAMPLE shock: +5 days lead time → OTIF {delay['projected']['otif_pct']}% (Δ {delay['deltas']['otif_pct']} pp).",
        "",
        "## Recommended actions",
        "- Attack **Europe RDC** late-line pool ($5.37M). Split late vs short-ship.",
        "- Graph: Fan Shop is the largest late-$ supplier — dual-source is SAMPLE vendor policy, not a live contract.",
        "- Do not quote late $ as lost sales or recovered EBITDA.",
        "",
        "## Guardrails",
        "- Policies in knowledge/ are SAMPLE.",
        "- GraphRAG is NetworkX-style snapshot; Neo4j is not running unless you start it.",
        "- Simulation is linear SAMPLE elasticities, not a digital twin.",
        "",
    ]
    return "\n".join(lines)


def markdown_to_pdf(md: str) -> bytes:
    """Minimal single-page Helvetica PDF. Text only."""
    lines = []
    for raw in md.replace("**", "").split("\n"):
        while len(raw) > 90:
            cut = raw.rfind(" ", 0, 90)
            if cut < 20:
                cut = 90
            lines.append(raw[:cut])
            raw = raw[cut:].lstrip()
        lines.append(raw if raw else " ")
    lines = lines[:60]
    cmds = ["BT", "/F1 11 Tf", "14 TL", "50 780 Td"]
    for i, line in enumerate(lines):
        safe = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        cmds.append(f"({safe}) Tj" if i == 0 else f"T* ({safe}) Tj")
    cmds.append("ET")
    stream = "\n".join(cmds)
    objects = [
        "1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj",
        "2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj",
        "3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj",
        f"4 0 obj << /Length {len(stream)} >> stream\n{stream}\nendstream endobj",
        "5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj",
    ]
    pdf = "%PDF-1.4\n"
    xref = [0]
    for obj in objects:
        xref.append(len(pdf))
        pdf += obj + "\n"
    startxref = len(pdf)
    pdf += f"xref\n0 {len(objects) + 1}\n"
    pdf += "0000000000 65535 f \n"
    for off in xref[1:]:
        pdf += f"{off:010d} 00000 n \n"
    pdf += f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{startxref}\n%%EOF"
    return pdf.encode("latin-1", errors="replace")
