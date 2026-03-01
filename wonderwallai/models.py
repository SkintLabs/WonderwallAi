"""
WonderwallAi — Data Models
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Verdict:
    """
    Result of a firewall scan.

    Attributes:
        allowed: Whether the message is allowed through.
        action: One of ``"allow"``, ``"block"``, ``"redact"``.
        blocked_by: Name of the layer that blocked (None if allowed).
        message: For outbound scans, the (possibly cleaned) text.
                 For blocked inbound, the user-facing block message.
        violations: List of violation codes (e.g. ``"CANARY_TOKEN_LEAK"``).
        scores: Layer-specific scores (e.g. ``{"semantic": 0.72}``).
    """

    allowed: bool
    action: str = "allow"
    blocked_by: Optional[str] = None
    message: str = ""
    violations: List[str] = field(default_factory=list)
    scores: Dict[str, float] = field(default_factory=dict)
