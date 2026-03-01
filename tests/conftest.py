"""
Shared fixtures for WonderwallAi tests.
"""

import numpy as np
import pytest


class FakeEmbeddingModel:
    """
    Deterministic embedding model for tests.
    Returns 384-dim vectors derived from text hash so that similar
    texts produce similar (but not identical) vectors.
    """

    def encode(self, texts, normalize_embeddings=False):
        embeddings = []
        for text in texts:
            # Create a deterministic seed from the text
            seed = sum(ord(c) for c in text) % (2**31)
            rng = np.random.RandomState(seed)
            vec = rng.randn(384).astype(np.float32)
            if normalize_embeddings:
                vec = vec / np.linalg.norm(vec)
            embeddings.append(vec)
        return np.array(embeddings)


@pytest.fixture
def mock_embedding_model():
    """Fake SentenceTransformer that returns deterministic embeddings."""
    return FakeEmbeddingModel()


@pytest.fixture
def sample_topics():
    return [
        "I want to buy a product from this store",
        "Help me track my order",
        "What is your return policy",
        "Hello hi greetings",
    ]
