"""
MeatHead — Human Entropy Module
Applies subtle, capped typing imperfections to make AI output pass as human.
Max 1 typo per generation. Never mutates URLs, product names, or commands.
"""

import random
import re

# QWERTY keyboard neighbor map (lowercase only)
NEIGHBORS = {
    'a': 's', 's': 'adw', 'd': 'sfe', 'f': 'dgr', 'g': 'fht',
    'h': 'gjyb', 'j': 'hknu', 'k': 'jloi', 'l': 'kop',
    'q': 'w', 'w': 'qeas', 'e': 'wrdsq', 'r': 'etdf', 't': 'ryfg',
    'y': 'tugh', 'u': 'yijh', 'i': 'uojk', 'o': 'ipkl', 'p': 'o',
    'z': 'x', 'x': 'zcsq', 'c': 'xvdf', 'v': 'cbgf', 'b': 'vnhg',
    'n': 'bmjh', 'm': 'njk',
}

# Words/patterns that must never be mutated
PROTECTED = {"http", "https", "wonderwall", "wonderwallai", "jerry", "skint", "skintlabs", "github", "shopify"}


def fat_finger_mistake(text: str, error_rate: float = 0.002, max_errors: int = 1) -> str:
    """Randomly swap a character for a keyboard neighbor, strictly capped."""
    words = text.split()
    new_words = []
    errors_made = 0

    for word in words:
        lower = word.lower()
        # Skip short words, protected terms, and once we hit the cap
        if (len(word) > 3
                and not any(p in lower for p in PROTECTED)
                and errors_made < max_errors):
            if random.random() < error_rate:
                idx = random.randint(1, len(word) - 2)
                char = word[idx].lower()
                if char in NEIGHBORS:
                    replacement = random.choice(NEIGHBORS[char])
                    if word[idx].isupper():
                        replacement = replacement.upper()
                    word = word[:idx] + replacement + word[idx + 1:]
                    errors_made += 1

        new_words.append(word)

    return " ".join(new_words)


def apply_human_entropy(text: str) -> str:
    """Run lazy typing filters over validated AI output with strict probability limits."""
    # 1. Inject a maximum of 1 typo per generation
    text = fat_finger_mistake(text)

    # 2. Lowercase start of sentence occasionally (10% chance, after commas only)
    if random.random() < 0.10:
        text = re.sub(r'(,\s+)([A-Z])', lambda m: m.group(1) + m.group(2).lower(), text, count=1)

    # 3. Replace formal colons with trailing thoughts (but not in URLs)
    text = re.sub(r'(?<!http)(?<!https):\s', '... ', text)

    # 4. Remove excessive enthusiasm
    text = text.replace("!", ".")

    return text
