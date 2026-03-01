"""Admin endpoints — create and manage API keys."""

import logging
import secrets
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select

from server.auth import hash_api_key
from server.config import get_settings
from server.db.engine import get_db
from server.db.models import ApiKey
from server.rate_limiter import PLAN_LIMITS

logger = logging.getLogger("wonderwallai.server.admin")

router = APIRouter(prefix="/admin", tags=["Admin"])

ADMIN_HEADER = "X-Admin-API-Key"


async def _verify_admin(request: Request) -> None:
    """Verify the admin API key from request headers."""
    settings = get_settings()
    api_key = request.headers.get(ADMIN_HEADER, "")
    if api_key != settings.admin_api_key:
        raise HTTPException(status_code=401, detail="Invalid admin API key")


# --- Request/Response Models ---


class CreateKeyRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    owner_email: str = Field(..., min_length=3, max_length=255)
    plan: str = Field(default="free")


class CreateKeyResponse(BaseModel):
    api_key: str  # Raw key — shown ONCE, never stored
    key_prefix: str
    name: str
    plan: str
    rate_limit: int


class KeyInfo(BaseModel):
    key_prefix: str
    name: str
    owner_email: str
    plan: str
    rate_limit: int
    is_active: bool
    created_at: str
    last_used_at: Optional[str] = None


# --- Endpoints ---


@router.post("/keys", response_model=CreateKeyResponse)
async def create_api_key(req: CreateKeyRequest, request: Request):
    """Create a new customer API key. Returns the raw key once."""
    await _verify_admin(request)

    # Generate raw key: ww_live_<32 hex chars>
    raw_key = f"ww_live_{secrets.token_hex(16)}"
    key_hash = hash_api_key(raw_key)
    key_prefix = raw_key[:16]
    rate_limit = PLAN_LIMITS.get(req.plan, PLAN_LIMITS["free"])

    async with get_db() as db:
        api_key = ApiKey(
            key_hash=key_hash,
            key_prefix=key_prefix,
            name=req.name,
            owner_email=req.owner_email,
            plan=req.plan,
            rate_limit=rate_limit,
            is_active=True,
        )
        db.add(api_key)

    logger.info(f"Created API key {key_prefix}... for {req.owner_email} ({req.plan})")

    return CreateKeyResponse(
        api_key=raw_key,
        key_prefix=key_prefix,
        name=req.name,
        plan=req.plan,
        rate_limit=rate_limit,
    )


@router.get("/keys", response_model=list[KeyInfo])
async def list_api_keys(request: Request):
    """List all API keys (admin only)."""
    await _verify_admin(request)

    async with get_db() as db:
        result = await db.execute(select(ApiKey).order_by(ApiKey.created_at.desc()))
        keys = result.scalars().all()

    return [
        KeyInfo(
            key_prefix=k.key_prefix,
            name=k.name,
            owner_email=k.owner_email,
            plan=k.plan,
            rate_limit=k.rate_limit,
            is_active=k.is_active,
            created_at=k.created_at.isoformat() if k.created_at else "",
            last_used_at=k.last_used_at.isoformat() if k.last_used_at else None,
        )
        for k in keys
    ]
