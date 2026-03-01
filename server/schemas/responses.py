"""Pydantic response models for all API endpoints."""

from typing import Dict, List, Optional

from pydantic import BaseModel


class VerdictResponse(BaseModel):
    """Maps directly from SDK Verdict dataclass."""

    allowed: bool
    action: str  # "allow" | "block" | "redact"
    blocked_by: Optional[str] = None
    message: str = ""
    violations: List[str] = []
    scores: Dict[str, float] = {}
    latency_ms: float


class CanaryResponse(BaseModel):
    canary_token: str
    prompt_block: str


class FileSanitizeResponse(BaseModel):
    ok: bool
    message: str
    cleaned_size_bytes: int = 0


class UsageResponse(BaseModel):
    api_key_prefix: str
    plan: str
    period_start: str
    period_end: str
    total_requests: int
    requests_by_endpoint: Dict[str, int]
    blocked_count: int
    avg_latency_ms: float


class ConfigResponse(BaseModel):
    config_id: int
    config_hash: str
    topics: List[str]
    similarity_threshold: float
    sentinel_enabled: bool
    sentinel_model: str
    bot_description: str
    canary_prefix: str
    fail_open: bool
    block_message: str
    block_message_injection: str
    allowed_mime_types: Optional[List[str]] = None
    created_at: str
    updated_at: str
