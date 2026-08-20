# Inventory & Safety Stock Policy (SAMPLE)

> **Sample policy for NEXUS RAG demos.** Figures are illustrative thresholds.

## Coverage bands
- **Green**: 2–6 weeks of supply
- **Yellow**: 6–12 weeks (working-capital review)
- **Red**: > 12 weeks or stockout flag on A-class SKUs

## Reorder rules
1. A-class SKUs: reorder at ROP; prefer preferred vendors.
2. B-class: weekly batch; allow 1 missed cycle before escalation.
3. C-class: monthly; consolidate POs.

## When to escalate
- Network weeks-of-supply > 20 with OTIF < 50% → cash vs service tradeoff workshop.
- Stockout on A-class for > 3 consecutive days → expedite approved under freight policy.
