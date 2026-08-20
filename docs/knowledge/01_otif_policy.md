# OTIF Service Policy (SAMPLE)

> **Sample policy for NEXUS RAG demos.** Not a live corporate SOP.

## Definition
**OTIF** = On-Time In-Full. An order is OTIF when every line ships by the promised date and quantities match the ordered amount.

## Targets
| Segment | OTIF target | Escalation |
|---|---|---|
| Enterprise | ≥ 92% | VP Supply Chain within 48h of weekly miss |
| Mid-market | ≥ 88% | Regional ops manager |
| SMB | ≥ 85% | Warehouse lead |

## Investigation playbook
1. Confirm late vs short-ship split (on-time vs in-full).
2. Check carrier / mode mix for the affected warehouse.
3. Review inventory stockouts on top SKUs in the window.
4. If expedite share > 15%, open freight cost review.

## Evidence required
- SQL OTIF by warehouse/week
- Top late carriers
- Stockout SKUs overlapping late orders
