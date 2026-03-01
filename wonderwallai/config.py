"""
WonderwallAi — Configuration
Centralizes all configurable parameters for the firewall SDK.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set


@dataclass
class WonderwallConfig:
    """
    Configuration for a Wonderwall firewall instance.

    All parameters have sensible defaults. At minimum, provide ``topics``
    to enable the semantic router.

    Example::

        from wonderwallai import Wonderwall
        from wonderwallai.patterns.topics import ECOMMERCE_TOPICS

        wall = Wonderwall(topics=ECOMMERCE_TOPICS)
    """

    # --- Semantic Router ------------------------------------------------
    topics: List[str] = field(default_factory=list)
    """Allowed conversation topics. Empty list disables semantic routing."""

    similarity_threshold: float = 0.35
    """Minimum cosine similarity to an allowed topic (0.0–1.0)."""

    embedding_model_name: str = "all-MiniLM-L6-v2"
    """SentenceTransformer model name. Used only when ``embedding_model`` is None."""

    embedding_model: Any = None
    """Pre-loaded SentenceTransformer instance (optional, avoids duplicate memory)."""

    # --- Sentinel Scan --------------------------------------------------
    sentinel_enabled: bool = True
    """Enable the LLM-based prompt injection classifier."""

    sentinel_api_key: str = ""
    """Groq API key. Falls back to ``GROQ_API_KEY`` env var if empty."""

    sentinel_model: str = "llama-3.1-8b-instant"
    """Model for the sentinel binary classifier."""

    bot_description: str = "an AI assistant"
    """Short description used in the sentinel system prompt template."""

    sentinel_system_prompt: Optional[str] = None
    """Full override for the sentinel system prompt. If set, ``bot_description`` is ignored."""

    # --- Egress Filter --------------------------------------------------
    canary_prefix: str = "WONDERWALL-"
    """Prefix for canary tokens injected into LLM system prompts."""

    api_key_patterns: List[Any] = field(default_factory=list)
    """Additional compiled regex patterns for API key detection (extends defaults)."""

    pii_patterns: Dict[str, Any] = field(default_factory=dict)
    """Additional PII patterns as ``{name: compiled_regex}`` (extends defaults)."""

    include_default_patterns: bool = True
    """If True, merge user-provided patterns with built-in defaults."""

    # --- File Sanitizer -------------------------------------------------
    allowed_mime_types: Set[str] = field(
        default_factory=lambda: {"image/jpeg", "image/png"}
    )
    """MIME types allowed for file uploads (validated by magic bytes)."""

    # --- Behavior -------------------------------------------------------
    fail_open: bool = True
    """If True, errors in any layer allow the message through (fail-open).
    If False, errors block the message (fail-closed)."""

    block_message: str = (
        "I can only help with topics I'm designed for. Could you rephrase?"
    )
    """Message returned when the semantic router blocks an off-topic query."""

    block_message_injection: str = "Could you rephrase your question?"
    """Message returned when the sentinel detects a prompt injection."""

    block_message_egress: str = (
        "I apologize, but I'm unable to process that request."
    )
    """Message returned when the egress filter hard-blocks a response (canary leak)."""
