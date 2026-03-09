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

        # 1. Check if the key exists
        if not api_key:
            logger.warning(f"Auth failed: Invalid key hash {key_hash[:8]}...")
            raise HTTPException(status_code=401, detail="Invalid API key")

        # 2. Check if the key is globally deactivated
        if not api_key.is_active:
            raise HTTPException(status_code=403, detail="API key deactivated")

        # 3. Billing Logic: Allow Early Birds or Active Subscriptions
        # If not an early bird, check the Stripe billing status
        if not getattr(api_key, "has_early_bird", False):
            status = getattr(api_key, "billing_status", "none")
            
            # Allow 'active' and 'trialing'. Block 'past_due', 'canceled', 'unpaid', or 'none'.
            if status not in ["active", "trialing"]:
                logger.info(f"Auth blocked: Key {api_key.id} has status '{status}'")
                raise HTTPException(
                    status_code=402, 
                    detail=f"Payment required. Your current subscription status is: {status}"
                )

        # 4. Update last_used_at
        await db.execute(
            update(ApiKey)
            .where(ApiKey.id == api_key.id)
            .values(last_used_at=sql_func.now())
        )

    return api_key
