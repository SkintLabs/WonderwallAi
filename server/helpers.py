"""Shared helpers used across API endpoints."""

import logging
from typing import Optional

from sqlalchemy import select

from server.db.engine import get_db
from server.db.models import ApiKey, FirewallConfig, UsageRecord
from server.instance_cache import compute_config_hash, get_or_create_instance
from wonderwallai import Wonderwall

logger = logging.getLogger("wonderwallai.server.helpers")


async def get_wonderwall_for_key(api_key: ApiKey) -> Wonderwall:
    """Load the FirewallConfig for an API key and return a cached Wonderwall instance."""
    async with get_db() as db:
        result = await db.execute(
            select(FirewallConfig).where(FirewallConfig.api_key_id == api_key.id)
        )
        config = result.scalar_one_or_none()

    if not config:
        # Use default config if none set
        default_dict = {
            "topics": [],
            "similarity_threshold": 0.35,
            "sentinel_enabled": True,
            "sentinel_model": "llama-3.1-8b-instant",
            "bot_description": "an AI assistant",
            "canary_prefix": "WONDERWALL-",
            "fail_open": True,
            "block_message": "I can only help with topics I'm designed for. Could you rephrase?",
            "block_message_injection": "Could you rephrase your question?",
            "allowed_mime_types": None,
        }
        config_hash = compute_config_hash(default_dict)
        return get_or_create_instance(config_hash, default_dict)

    config_dict = {
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

    return get_or_create_instance(config.config_hash, config_dict)


async def record_usage(
    api_key_id: int,
    endpoint: str,
    latency_ms: float,
    was_blocked: bool = False,
    blocked_by: Optional[str] = None,
) -> None:
    """Write a usage record for billing/analytics."""
    try:
        async with get_db() as db:
            db.add(
                UsageRecord(
                    api_key_id=api_key_id,
                    endpoint=endpoint,
                    latency_ms=latency_ms,
                    was_blocked=was_blocked,
                    blocked_by=blocked_by,
                )
            )
    except Exception as e:
        # Never let usage tracking break a scan request
        logger.error(f"Failed to record usage: {e}")
