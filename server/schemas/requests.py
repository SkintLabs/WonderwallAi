"""Pydantic request models for all API endpoints."""

from typing import List, Optional, Set

from pydantic import BaseModel, Field


class ScanInboundRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)


class ScanOutboundRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=50000)
    canary_token: str = ""


class CanaryGenerateRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=255)


class FirewallConfigRequest(BaseModel):
    topics: List[str] = []
    similarity_threshold: float = Field(default=0.35, ge=0.0, le=1.0)
    sentinel_enabled: bool = True
    sentinel_model: str = "llama-3.1-8b-instant"
    bot_description: str = "an AI assistant"
    canary_prefix: str = "WONDERWALL-"
    fail_open: bool = True
    block_message: str = (
        "I can only help with topics I'm designed for. Could you rephrase?"
    )
    block_message_injection: str = "Could you rephrase your question?"
    allowed_mime_types: Optional[List[str]] = None


class UpgradePlanRequest(BaseModel):
    new_plan: str = Field(..., pattern="^(starter|pro|business|enterprise)$")
