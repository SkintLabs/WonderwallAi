"""Wonderwall instance pool — shared embedding model, per-config caching."""

import hashlib
import json
import logging
from typing import Any, Dict, Optional

from wonderwallai import Wonderwall, WonderwallConfig

from server.config import get_settings

logger = logging.getLogger("wonderwallai.server.cache")

_instance_cache: Dict[str, Wonderwall] = {}
_shared_embedding_model: Any = None


def compute_config_hash(config_dict: dict) -> str:
    """Deterministic SHA-256 hash of a config dict for cache keying."""
    canonical = json.dumps(config_dict, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()


def warm_shared_model() -> None:
    """Pre-load the shared SentenceTransformer model at startup."""
    global _shared_embedding_model
    try:
        from sentence_transformers import SentenceTransformer

        _shared_embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("Shared embedding model loaded (all-MiniLM-L6-v2)")
    except ImportError:
        logger.warning("sentence-transformers not installed — semantic routing disabled")
    except Exception as e:
        logger.error(f"Failed to load embedding model: {e}")


def get_or_create_instance(config_hash: str, config_dict: dict) -> Wonderwall:
    """Return a cached Wonderwall instance or create a new one."""
    if config_hash in _instance_cache:
        return _instance_cache[config_hash]

    settings = get_settings()

    ww_config = WonderwallConfig(
        topics=config_dict.get("topics") or [],
        similarity_threshold=config_dict.get("similarity_threshold", 0.35),
        embedding_model=_shared_embedding_model,
        sentinel_enabled=config_dict.get("sentinel_enabled", True),
        sentinel_api_key=settings.groq_api_key,
        sentinel_model=config_dict.get("sentinel_model", "llama-3.1-8b-instant"),
        bot_description=config_dict.get("bot_description", "an AI assistant"),
        canary_prefix=config_dict.get("canary_prefix", "WONDERWALL-"),
        fail_open=config_dict.get("fail_open", True),
        block_message=config_dict.get("block_message", ""),
        block_message_injection=config_dict.get("block_message_injection", ""),
    )

    instance = Wonderwall(config=ww_config)
    _instance_cache[config_hash] = instance
    logger.info(f"Created Wonderwall instance for config {config_hash[:12]}...")
    return instance


def evict(config_hash: str) -> None:
    """Remove a cached instance (called when config is updated)."""
    if config_hash in _instance_cache:
        del _instance_cache[config_hash]
        logger.info(f"Evicted cached instance {config_hash[:12]}...")


def clear_cache() -> None:
    """Clear all cached instances (called on shutdown)."""
    _instance_cache.clear()
    logger.info("Instance cache cleared")


def is_model_loaded() -> bool:
    return _shared_embedding_model is not None


def get_cache_size() -> int:
    return len(_instance_cache)
