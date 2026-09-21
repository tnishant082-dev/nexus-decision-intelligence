# Production readiness and enterprise maturity

**Overall: 6.4 / 10 as a local portfolio platform. 4 / 10 as something you would put on a public network.**

v1.4 added GraphRAG snapshot, linear twin, gold-set eval, inference queue/retry, quality command, heuristic guardrails, JSON memory, and extract replay. None of that is a hosted control plane.

Details: `docs/repository-audit.md`, `docs/gap-analysis.md`, `docs/limitations.md`.

| Practice | Maturity | Notes |
|---|---|---|
| Product focus | High | One domain |
| Reproducible analytics | High | Parquet → DuckDB → views + snapshots |
| Testing | Medium | Pytest + CI warehouse + v1.4 snapshot tests |
| Documentation honesty | High | Explicit mock/SAMPLE/idle-adapter language |
| ML governance | Medium | File registry, drift job |
| Inference ops | Low–medium | Queue/retry/cache adapters, no fleet |
| Graph / twin | Low–medium | Snapshot + linear elasticities |
| Security | Low–medium | API key demo + heuristic guards |
| Reliability | Low | Single process, single file |
| Cost control | Medium | Cost fields default to 0 |
| Compliance | Low | Demo PII in `dim_customer` (not used in GraphRAG) |

Do not quote this file as a SOC2 or ISO result.
