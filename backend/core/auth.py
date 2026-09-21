from __future__ import annotations

from fastapi import Header, HTTPException, status

from backend.core.config import api_key_ok


async def require_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")):
    if not api_key_ok(x_api_key):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing X-API-Key")
    return x_api_key


async def optional_role(x_nexus_role: str | None = Header(default="viewer", alias="X-Nexus-Role")):
    role = (x_nexus_role or "viewer").lower()
    if role not in {"viewer", "analyst", "admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unknown role")
    return role
