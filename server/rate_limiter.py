"""Per-key in-memory rate limiting."""

import time
from collections import defaultdict

from fastapi import HTTPException

_timestamps: dict[int, list[float]] = defaultdict(list)

# Plan rate limits (requests per minute)
PLAN_LIMITS = {
    "free": 10,
    "starter": 60,
    "pro": 200,
    "business": 500,
    "enterprise": 1000,
}


def check_rate_limit(api_key_id: int, rate_limit: int, window: int = 60) -> None:
    """Raise 429 if the key has exceeded its per-minute limit."""
    now = time.time()
    cutoff = now - window

    # Prune old entries
    _timestamps[api_key_id] = [t for t in _timestamps[api_key_id] if t > cutoff]

    if len(_timestamps[api_key_id]) >= rate_limit:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded ({rate_limit} req/min). Upgrade your plan for higher limits.",
            headers={"Retry-After": str(window)},
        )

    _timestamps[api_key_id].append(now)


def clear_timestamps() -> None:
    """Clear all rate limit state (called on shutdown)."""
    _timestamps.clear()
