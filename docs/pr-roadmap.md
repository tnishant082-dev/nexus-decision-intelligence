# Pull-request roadmap

Prefer small, reviewable PRs. v1.3 (Wilson + HITL ledger) is on `main`. v1.4 is this increment.

| PR | Title | Includes |
|---|---|---|
| 1 | Wilson OTIF + HITL ledger | `decisions/wilson.py`, ledger history — **merged** |
| 2 | GraphRAG snapshot + retrieve | `ai/graphrag/**`, `artifacts/graph_snapshot.json` |
| 3 | Linear SAMPLE twin | `simulation/**` |
| 4 | Agent eval + guardrails | `evaluation/**`, `security/guardrails/**` |
| 5 | Inference queue/retry + copilot | `inference/queue.py`, `inference/retry.py`, `copilot/**` |
| 6 | Quality / memory / stream / observe | `quality/**`, `memory/**`, `streaming/**`, `observability/collect.py` |
| 7 | Docs + Streamlit tabs + API | `docs/**`, `frontend/streamlit_app.py`, `backend/main.py` |

This workspace ships **PR 2–7 as one reviewable squash** so numbers stay consistent (Fan Shop late-line, OTIF 40.83, quality 11/11). Split later if you want smaller diffs.

Do not merge README claims that CI has not run.
