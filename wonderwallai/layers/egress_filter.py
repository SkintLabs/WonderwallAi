"""
WonderwallAi — Egress Filter Layer
Scans LLM responses for leaked secrets, PII, and canary tokens
before they reach the end user.
"""

import hashlib
import logging
import re
from typing import Dict, List, Optional, Tuple

from wonderwallai.patterns.api_keys import DEFAULT_API_KEY_PATTERNS
from wonderwallai.patterns.pii import DEFAULT_PII_PATTERNS

logger = logging.getLogger("wonderwallai.egress_filter")


class EgressFilter:
    """
    Scans outbound LLM responses for leaked secrets, PII, and canary tokens.

    Protocols:
        A (Hard Stop): Canary token appears in output → block entire response.
        B (Sanitize): API keys or PII detected → redact and pass through.

    Args:
        canary_prefix: Prefix for generated canary tokens.
        api_key_patterns: Additional regex patterns for API key detection.
        pii_patterns: Additional PII patterns as ``{name: compiled_regex}``.
        include_defaults: Merge user patterns with built-in defaults.
        block_message: Message returned on canary token leak (hard stop).
    """

    def __init__(
        self,
        canary_prefix: str = "WONDERWALL-",
        api_key_patterns: Optional[List[re.Pattern]] = None,
        pii_patterns: Optional[Dict[str, re.Pattern]] = None,
        include_defaults: bool = True,
        block_message: str = "I apologize, but I'm unable to process that request.",
    ):
        self.canary_prefix = canary_prefix
        self.block_message = block_message

        # Build API key patterns
        self.api_key_patterns: List[re.Pattern] = []
        if include_defaults:
            self.api_key_patterns.extend(DEFAULT_API_KEY_PATTERNS)
        if api_key_patterns:
            self.api_key_patterns.extend(api_key_patterns)

        # Build PII patterns
        self.pii_patterns: Dict[str, re.Pattern] = {}
        if include_defaults:
            self.pii_patterns.update(DEFAULT_PII_PATTERNS)
        if pii_patterns:
            self.pii_patterns.update(pii_patterns)

    def generate_canary_token(self, session_id: str) -> str:
        """Generate a unique canary token for a session."""
        h = hashlib.sha256(session_id.encode()).hexdigest()[:16]
        return f"{self.canary_prefix}{h}"

    def scan(self, text: str, canary_token: str) -> Tuple[bool, str, List[str]]:
        """
        Scan outbound text for security violations.

        Returns:
            Tuple of (is_safe, cleaned_text, list_of_violations).
        """
        violations: List[str] = []
        cleaned = text

        # Protocol A: Canary token detection (prompt injection confirmed)
        if canary_token and canary_token in text:
            violations.append("CANARY_TOKEN_LEAK")
            logger.critical(
                "CANARY TOKEN DETECTED in outbound response — "
                "prompt injection attack succeeded. Blocking response."
            )
            return (False, self.block_message, violations)

        # Protocol B: API key leak detection
        for pattern in self.api_key_patterns:
            if pattern.search(cleaned):
                violations.append(f"API_KEY_LEAK:{pattern.pattern[:30]}")
                cleaned = pattern.sub("[REDACTED]", cleaned)
                logger.critical("API key leak detected and redacted in outbound response")

        # Protocol B: PII sanitization
        for pii_type, pattern in self.pii_patterns.items():
            if pattern.search(cleaned):
                violations.append(f"PII:{pii_type}")
                cleaned = pattern.sub(f"[{pii_type.upper()}_REDACTED]", cleaned)
                logger.warning(f"PII ({pii_type}) redacted from outbound response")

        # Only hard-block on canary leak (Protocol A).
        # Redactions (Protocol B) are safe — the cleaned text is returned.
        return (True, cleaned, violations)
