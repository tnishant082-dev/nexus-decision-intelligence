# Simulation architecture

`simulation/engine.py` applies **SAMPLE linear elasticities** to extract KPI baselines.

It is **not** a digital twin: it does not resimulate orders, warehouse fill, or carrier capacity.

| Shock | Knobs | Primary effects |
|---|---|---|
| Inventory +/- | `pct` | OTIF ±0.08 pp per %, holding-cost proxy on extra on-hand $ |
| Supplier delay | `days` | OTIF −1.8 pp/day, late-line $ +3.5%/day |
| Demand surge | `pct` | Revenue 1:1, stockout +0.22 pp per %, OTIF −0.12 pp per % |
| Price +/- | `pct` | SAMPLE elasticity −0.55 on quantity |
| Promotion | on | +12% units, −1.5 pp margin |

Baselines (extract window 2015-01-01 → 2018-01-31):

- Revenue $31,644,665.08
- OTIF 40.83%
- Late-line revenue $18,082,555.30
- SAMPLE OTIF cap 92%

Worked example: inventory +20% → OTIF 42.43% (40.83 + 1.60). Lead time +5 days → OTIF 31.83%.
