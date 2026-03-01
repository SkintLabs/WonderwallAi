"""Health check endpoint — no auth required."""

from fastapi import APIRouter

from wonderwallai._version import __version__

from server.config import get_settings

router = APIRouter(tags=["System"])


@router.get("/v1/health")
async def health():
    """Returns 200 even when degraded, with service status details."""
    settings = get_settings()

    # Lazy import to avoid circular deps
    from server.instance_cache import get_cache_size, is_model_loaded

    return {
        "status": "healthy",
        "version": __version__,
        "environment": settings.environment,
        "embedding_model": "loaded" if is_model_loaded() else "not_loaded",
        "sentinel": "available" if settings.groq_api_key else "no_api_key",
        "database": "sqlite" if "sqlite" in settings.database_url else "postgresql",
        "cached_instances": get_cache_size(),
    }
