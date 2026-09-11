# Security Notes (local portfolio)

- **API key**: `NEXUS_API_KEY` (default `dev-nexus-key`) required on `/api/v1/*`.
- **Rate limit**: in-memory ~60 req/min per key/IP — demo only, not distributed.
- **SQL tool**: SELECT/WITH only; blocks DDL/DML keywords.
- **PII**: `dim_customer` includes names from the public extract — treat as demo data; do not deploy publicly without redaction.
- **Secrets**: no cloud keys required for the mock path. Do not commit real provider keys.
- **Docker**: binds localhost ports; do not expose without auth hardening.
