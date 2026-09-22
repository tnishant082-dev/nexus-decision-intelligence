# Inferential engineering

This is not the LLM gateway. That path lives in [`inference.md`](./inference.md). Inferential engineering decides whether a contrast is allowed to drive an action.

Each registered study runs the same six steps:

1. **Estimand** — unit, outcome, contrast, population, adjustment set.
2. **Identification** — what the design can support. A causal claim stays false unless the design earns it. Neither study in this repo earns one.
3. **Estimator** — inverse-variance stratified risk difference. Strata with fewer than 20 units on either arm are dropped.
4. **Uncertainty** — normal 95% interval on the adjusted risk difference.
5. **Sensitivity** — nullification bias (how large a constant shift must be before the interval covers zero) and a crude-rate E-value. The E-value describes the unadjusted rates, not the stratified contrast.
6. **Decision** — `prioritize` only when the whole interval sits above a 2 percentage-point practical threshold **and** identification does not forbid the claim. Otherwise `hold`, `do_not_prioritize`, or `do_not_claim`.

## Registered studies

| Id | Contrast | What it is allowed to say |
|---|---|---|
| `warehouse_late_gap` | Late rate at the warehouse with the largest late-line revenue pool, versus the rest of the network, adjusted for the order's dominant product category | Rank that warehouse for investigation. Not the effect of moving orders. |
| `advance_selection` | Late rate on `is_advance` shipments versus other shipments, adjusted for warehouse | The numbers are reported, then the verdict is `do_not_claim`. Advance shipping is chosen when delay risk is already high. |

Order grain for the warehouse study: an order is late if any line is late. The stratum is the product category with the most line sales on that order.

## Where it runs

- `GET /api/v1/inferential/board`
- `GET /api/v1/inferential/studies/{study_id}`
- Streamlit tab **Inferential**
- One sentence on the investigate response and in the Monday brief

Practical threshold and minimum cell size are constants in `inferential/studies.py`, not knobs on the request. Changing them is a design change, not a dashboard toggle.

## What this will not say

- Late-rate gaps are not recovered EBITDA.
- A small p-value is not identification.
- Category adjustment does not control carrier, season, or customer mix.
- The LLM Inference Monitor does not compute these intervals.
