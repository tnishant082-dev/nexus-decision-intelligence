# Security notes (local portfolio)

- **API key:** `NEXUS_API_KEY` compared with `hmac.compare_digest`. Default `dev-nexus-key` is for localhost only.
- **Roles:** `X-Nexus-Role` = `viewer` (default) | `analyst` | `admin`. Viewers cannot use `/api/v1/sql`.
- **CORS:** allow-list from `NEXUS_CORS_ORIGINS` (defaults to local Streamlit), not `*`.
- **Rate limit:** in-memory ~60 req/min per key/IP — not distributed.
- **SQL tool:** SELECT/WITH only; keyword filter is not a full sandbox.
- **Audit:** `monitoring/audit.sqlite` when `NEXUS_AUDIT=1`.
- **PII:** `dim_customer` includes names from the public extract — demo data; do not expose publicly without redaction.
- **Secrets:** provider keys via environment only. Do not commit `.env`.
- **Docker:** do not publish ports without rotating the key and tightening CORS.
