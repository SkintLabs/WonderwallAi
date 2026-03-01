"""
WonderwallAi — Built-in API Key Patterns
Regex patterns for detecting leaked API keys in LLM responses.
"""

import re

DEFAULT_API_KEY_PATTERNS = [
    re.compile(r'shpat_[a-fA-F0-9]{32,}'),       # Shopify access tokens
    re.compile(r'shpss_[a-fA-F0-9]{32,}'),        # Shopify API secrets
    re.compile(r'sk-[a-zA-Z0-9]{20,}'),           # OpenAI API keys
    re.compile(r'gsk_[a-zA-Z0-9]{20,}'),          # Groq API keys
    re.compile(r'pcsk_[a-zA-Z0-9]{20,}'),         # Pinecone API keys
    re.compile(r'sk_live_[a-zA-Z0-9]{20,}'),      # Stripe live keys
    re.compile(r'sk_test_[a-zA-Z0-9]{20,}'),      # Stripe test keys
    re.compile(r'whsec_[a-zA-Z0-9]{20,}'),        # Stripe webhook secrets
    re.compile(r'ghp_[a-zA-Z0-9]{36,}'),          # GitHub personal access tokens
    re.compile(r'AKIA[0-9A-Z]{16}'),              # AWS access key IDs
]
