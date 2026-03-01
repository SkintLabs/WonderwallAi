# WonderwallAi

AI firewall SDK for LLM applications. Protect against prompt injection, data leaks, and off-topic abuse.

## What It Does

WonderwallAi sits between your users and your LLM, scanning messages in both directions:

**Inbound (user to LLM):**
- **Semantic Router** — Blocks off-topic queries using vector similarity against your allowed topics
- **Sentinel Scan** — Detects prompt injection attacks using a fast LLM classifier (Groq)

**Outbound (LLM to user):**
- **Egress Filter** — Catches leaked API keys, PII, and canary tokens before they reach the user
- **File Sanitizer** — Validates uploads by magic bytes and strips EXIF metadata

All layers are fail-open by default — errors allow messages through rather than blocking legitimate users.

## Installation

```bash
# Lightweight (egress filter only — no ML dependencies)
pip install wonderwallai

# Full install (all layers including semantic routing + sentinel)
pip install wonderwallai[all]

# Individual layers
pip install wonderwallai[semantic]   # + sentence-transformers + torch
pip install wonderwallai[sentinel]   # + groq
pip install wonderwallai[files]      # + Pillow + filetype
```

## Quick Start

```python
from wonderwallai import Wonderwall
from wonderwallai.patterns.topics import ECOMMERCE_TOPICS

wall = Wonderwall(
    topics=ECOMMERCE_TOPICS,
    sentinel_api_key="gsk_...",
    bot_description="a customer service chatbot for an online store",
)

# Scan user input before it reaches your LLM
verdict = await wall.scan_inbound(user_message)
if not verdict.allowed:
    return verdict.message  # User-friendly rejection

# Generate a canary token and inject it into your LLM system prompt
canary = wall.generate_canary(session_id)
system_prompt += wall.get_canary_prompt(canary)

# Scan LLM output before it reaches the user
verdict = await wall.scan_outbound(llm_response, canary)
response_text = verdict.message  # Cleaned text (API keys/PII redacted)
```

## Configuration

All parameters have sensible defaults. Pass them as keyword arguments or use a `WonderwallConfig` object:

```python
from wonderwallai import Wonderwall, WonderwallConfig

# Keyword arguments
wall = Wonderwall(
    topics=["Order tracking", "Returns", "Product questions"],
    similarity_threshold=0.35,
    sentinel_api_key="gsk_...",
    sentinel_model="llama-3.1-8b-instant",
    bot_description="a customer service chatbot",
    canary_prefix="MYAPP-",
    fail_open=True,
    block_message="I can only help with topics I'm designed for.",
)

# Or use a config object
config = WonderwallConfig(topics=["..."], ...)
wall = Wonderwall(config=config)
```

### Key Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `topics` | `[]` | Allowed conversation topics. Empty disables semantic routing. |
| `similarity_threshold` | `0.35` | Cosine similarity threshold (0.0-1.0). |
| `embedding_model` | `None` | Pre-loaded SentenceTransformer instance (saves memory). |
| `sentinel_api_key` | `""` | Groq API key. Falls back to `GROQ_API_KEY` env var. |
| `sentinel_model` | `"llama-3.1-8b-instant"` | Model for the sentinel classifier. |
| `bot_description` | `"an AI assistant"` | Used in the sentinel system prompt. |
| `canary_prefix` | `"WONDERWALL-"` | Prefix for generated canary tokens. |
| `fail_open` | `True` | Allow messages through on errors (vs block). |
| `block_message` | Generic | Message shown when semantic router blocks. |
| `block_message_injection` | Generic | Message shown when sentinel blocks. |

## Pre-Built Topic Sets

```python
from wonderwallai.patterns.topics import (
    ECOMMERCE_TOPICS,   # 18 shopping/order topics
    SUPPORT_TOPICS,     # 13 technical support topics
    SAAS_TOPICS,        # 14 SaaS product topics
)

# Combine topic sets
wall = Wonderwall(topics=ECOMMERCE_TOPICS + SUPPORT_TOPICS)
```

## Custom Patterns

Extend the built-in API key and PII detection patterns:

```python
import re
from wonderwallai.patterns.api_keys import DEFAULT_API_KEY_PATTERNS

wall = Wonderwall(
    api_key_patterns=[re.compile(r'myapp_[a-zA-Z0-9]{32}')],
    pii_patterns={"employee_id": re.compile(r'EMP-\d{6}')},
    include_default_patterns=True,  # Merge with built-in patterns
)
```

## How the Verdict Works

Every scan returns a `Verdict` object:

```python
verdict = await wall.scan_inbound(message)

verdict.allowed      # bool — True if message passes
verdict.action       # "allow" | "block" | "redact"
verdict.blocked_by   # "semantic_router" | "sentinel_scan" | "egress_filter" | None
verdict.message      # The (possibly cleaned) text or block message
verdict.violations   # List of violation codes
verdict.scores       # Layer scores, e.g. {"semantic": 0.72}
```

## Architecture

```
User Message
    |
    v
[Semantic Router] ---> cosine similarity vs allowed topics (sub-ms)
    |
    v
[Sentinel Scan] -----> LLM binary classifier via Groq (~100ms)
    |
    v
Your LLM (GPT, Claude, Llama, etc.)
    |
    v
[Egress Filter] -----> canary tokens, API keys, PII detection
    |
    v
User Response (cleaned)
```

## License

MIT
