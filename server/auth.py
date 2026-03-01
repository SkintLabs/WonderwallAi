"""API key authentication — Bearer token → DB lookup."""

import hashlib
import logging

from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select, update
from sqlalchemy import func as sql_func

from server.db.engine import get_db
from server.db.models import ApiKey

logger = logging.getLogger("wonderwallai.server.auth")

_bearer_scheme = HTTPBearer()


def hash_api_key(raw_key: str) -> str:
    """SHA-256 hash of the raw API key for secure storage."""
    return hashlib.sha256(raw_key.encode()).hexdigest()


async def get_current_api_key(
    credentials: HTTPAuthorizationCredentials = Security(_bearer_scheme),
) -> ApiKey:
    """FastAPI dependency: validate Bearer token and return the ApiKey row."""
    key_hash = hash_api_key(credentials.credentials)

    async with get_db() as db:
        result = await db.execute(select(ApiKey).where(ApiKey.key_hash == key_hash))
        api_key = result.scalar_one_or_none()

        if not api_key:
            raise HTTPException(status_code=401, detail="Invalid API key")
        if not api_key.is_active:
            raise HTTPException(status_code=403, detail="API key deactivated")

        # Update last_used_at
        await db.execute(
            update(ApiKey)
            .where(ApiKey.id == api_key.id)
            .values(last_used_at=sql_func.now())
        )

    return api_key
