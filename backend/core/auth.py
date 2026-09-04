
from __future__ import annotations
from fastapi import Header, HTTPException, status
from backend.core.config import API_KEY

async def require_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")):
    if not x_api_key or x_api_key != API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing X-API-Key")
    return x_api_key
