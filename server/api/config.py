"""Firewall config CRUD — per API key."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from server.auth import get_current_api_key
from server.db.engine import get_db
from server.db.models import ApiKey, FirewallConfig
from server.instance_cache import compute_config_hash, evict, get_or_create_instance
from server.schemas.requests import FirewallConfigRequest
from server.schemas.responses import ConfigResponse

logger = logging.getLogger("wonderwallai.server.config")

router = APIRouter(prefix="/v1/config", tags=["Config"])


def _config_to_dict(config: FirewallConfig) -> dict:
    """Convert a FirewallConfig DB row to the dict used by instance_cache."""
    return {
        "topics": config.topics or [],
        "similarity_threshold": config.similarity_threshold,
        "sentinel_enabled": config.sentinel_enabled,
        "sentinel_model": config.sentinel_model,
        "bot_description": config.bot_description,
        "canary_prefix": config.canary_prefix,
        "fail_open": config.fail_open,
        "block_message": config.block_message,
        "block_message_injection": config.block_message_injection,
        "allowed_mime_types": config.allowed_mime_types,
    }


def _config_response(config: FirewallConfig) -> ConfigResponse:
    return ConfigResponse(
        config_id=config.id,
        config_hash=config.config_hash,
        topics=config.topics or [],
        similarity_threshold=config.similarity_threshold,
        sentinel_enabled=config.sentinel_enabled,
        sentinel_model=config.sentinel_model,
        bot_description=config.bot_description,
        canary_prefix=config.canary_prefix,
        fail_open=config.fail_open,
        block_message=config.block_message,
        block_message_injection=config.block_message_injection,
        allowed_mime_types=config.allowed_mime_types,
        created_at=config.created_at.isoformat() if config.created_at else "",
        updated_at=config.updated_at.isoformat() if config.updated_at else "",
    )


@router.post("/", response_model=ConfigResponse)
async def create_or_update_config(
    req: FirewallConfigRequest,
    api_key: ApiKey = Depends(get_current_api_key),
):
    """Create or update the firewall configuration for this API key."""
    config_dict = req.model_dump()
    config_hash = compute_config_hash(config_dict)

    async with get_db() as db:
        result = await db.execute(
            select(FirewallConfig).where(FirewallConfig.api_key_id == api_key.id)
        )
        existing = result.scalar_one_or_none()

        if existing:
            old_hash = existing.config_hash
            # Update all fields
            existing.topics = config_dict["topics"]
            existing.similarity_threshold = config_dict["similarity_threshold"]
            existing.sentinel_enabled = config_dict["sentinel_enabled"]
            existing.sentinel_model = config_dict["sentinel_model"]
            existing.bot_description = config_dict["bot_description"]
            existing.canary_prefix = config_dict["canary_prefix"]
            existing.fail_open = config_dict["fail_open"]
            existing.block_message = config_dict["block_message"]
            existing.block_message_injection = config_dict["block_message_injection"]
            existing.allowed_mime_types = config_dict["allowed_mime_types"]
            existing.config_hash = config_hash
            # Evict old cached instance
            evict(old_hash)
            config = existing
        else:
            config = FirewallConfig(
                api_key_id=api_key.id,
                config_hash=config_hash,
                **config_dict,
            )
            db.add(config)
            await db.flush()

    # Pre-warm the new instance
    get_or_create_instance(config_hash, config_dict)

    logger.info(f"Config updated for key {api_key.key_prefix} → {config_hash[:12]}")
    return _config_response(config)


@router.get("/", response_model=ConfigResponse)
async def get_config(api_key: ApiKey = Depends(get_current_api_key)):
    """Read the current firewall configuration for this API key."""
    async with get_db() as db:
        result = await db.execute(
            select(FirewallConfig).where(FirewallConfig.api_key_id == api_key.id)
        )
        config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=404,
            detail="No firewall config found. Create one with POST /v1/config",
        )

    return _config_response(config)
