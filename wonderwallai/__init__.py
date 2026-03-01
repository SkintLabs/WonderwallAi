"""
WonderwallAi — AI Firewall SDK
Protect LLM applications from prompt injection, data leaks, and off-topic abuse.

Quick start::

    from wonderwallai import Wonderwall

    wall = Wonderwall(
        topics=["Product questions", "Order tracking", "Returns"],
        sentinel_api_key="gsk_...",
    )

    verdict = await wall.scan_inbound(user_message)
    if not verdict.allowed:
        return verdict.message
"""

from wonderwallai._version import __version__
from wonderwallai.client import Wonderwall
from wonderwallai.config import WonderwallConfig
from wonderwallai.models import Verdict

__all__ = ["Wonderwall", "WonderwallConfig", "Verdict", "__version__"]
