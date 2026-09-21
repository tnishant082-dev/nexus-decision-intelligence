# What makes NEXUS unique (business impact)

Most portfolio “control towers” stop at KPI tiles. NEXUS is built so an operator **ranks work by dollars**, not by whichever chart is red.

## The distinctive loop

1. **Value at stake** — late-line revenue, delay_cost, expedite freight, snapshot unfilled_value, inactivity LTV proxy.
2. **Exception queue** — warehouses/carriers sorted by **$**, with SAMPLE policy citations and an owner.
3. **Linear scenarios** — “close 25% of this node’s late-line pool” sizes the work; it is **not** a digital twin.
4. **Investigate** — SQL + RAG + models, plus the same $ pool so the answer is not generic OTIF advice.
5. **Ledger** — propose / accept / reject / done locally (Monday ops workflow).
6. **Brief** — markdown pack an ops lead could paste into a standup.

## What we refuse to claim

- Late revenue is **not** lost sales or recovered EBITDA.
- Expedite cuts can **hurt** OTIF; the UI says so.
- SAMPLE 92% OTIF is a demo policy, not this retailer’s contract.
- 2018 is a stub month; YoY uses **2016 vs 2017** only.

## Why this extract is a good stress test

OTIF in the warehouse is far below the SAMPLE enterprise target, so the service-risk pool is large relative to delay_cost and unfilled_value. That ranking is the product insight: **do not optimize freight pennies while late-line revenue dominates**.

Recompute anytime:

```bash
python -c "from decisions.economics import value_at_stake; print(value_at_stake())"
```
