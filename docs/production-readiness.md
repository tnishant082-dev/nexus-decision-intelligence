# Production readiness and enterprise maturity

**Overall: 6.2 / 10 as a local portfolio platform. 4 / 10 as something you would put on a public network.**

Details: `docs/repository-audit.md`, `docs/gap-analysis.md`.

| Practice | Maturity | Notes |
|---|---|---|
| Product focus | High | One domain |
| Reproducible analytics | High | Parquet → DuckDB → views |
| Testing | Medium | Pytest + CI warehouse |
| Documentation honesty | High | Explicit mock/SAMPLE language |
| ML governance | Medium | File registry, drift job |
| Inference ops | Low–medium | Adapters, no fleet |
| Security | Low–medium | API key demo |
| Reliability | Low | Single process, single file |
| Cost control | Medium | Cost fields default to 0 |
| Compliance | Low | Demo PII in `dim_customer` |

Do not quote this file as a SOC2 or ISO result.
