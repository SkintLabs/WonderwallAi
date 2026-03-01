"""
WonderwallAi — Built-in PII Patterns
Regex patterns for detecting personally identifiable information in LLM responses.
"""

import re

DEFAULT_PII_PATTERNS = {
    "credit_card": re.compile(r'\b(?:\d{4}[-\s]?){3}\d{1,4}\b'),
    "ssn": re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
    "email": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
    "phone_us": re.compile(r'\b(?:\+1[-.]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'),
}
