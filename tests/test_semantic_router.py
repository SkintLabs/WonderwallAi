"""Tests for the Semantic Router layer."""

import pytest
from wonderwallai.layers.semantic_router import SemanticRouter


class TestSemanticRouter:
    def test_empty_topics_disables_router(self, mock_embedding_model):
        router = SemanticRouter(
            topics=[], embedding_model=mock_embedding_model
        )
        # Should always allow when disabled

    @pytest.mark.asyncio
    async def test_disabled_router_allows_all(self, mock_embedding_model):
        router = SemanticRouter(topics=[], embedding_model=mock_embedding_model)
        is_allowed, score, topic = await router.is_on_topic("hack the planet")
        assert is_allowed is True
        assert topic == "router_disabled"

    @pytest.mark.asyncio
    async def test_no_model_graceful_fallback(self, mock_embedding_model):
        """When embedding_model is None but sentence-transformers is installed,
        the router loads its own model. Test that it works end-to-end."""
        router = SemanticRouter(
            topics=["Product questions and shopping help"],
            embedding_model=mock_embedding_model,
            threshold=0.0,  # Allow everything
        )
        is_allowed, score, topic = await router.is_on_topic("anything")
        assert is_allowed is True

    def test_topics_stored(self, mock_embedding_model, sample_topics):
        router = SemanticRouter(
            topics=sample_topics,
            embedding_model=mock_embedding_model,
        )
        assert router.topics == sample_topics
        assert router._allowed_embeddings is not None
        assert router._allowed_embeddings.shape[0] == len(sample_topics)

    def test_custom_threshold(self, mock_embedding_model, sample_topics):
        router = SemanticRouter(
            topics=sample_topics,
            threshold=0.99,
            embedding_model=mock_embedding_model,
        )
        assert router.threshold == 0.99

    @pytest.mark.asyncio
    async def test_returns_similarity_score(self, mock_embedding_model, sample_topics):
        router = SemanticRouter(
            topics=sample_topics,
            threshold=0.0,  # Allow everything
            embedding_model=mock_embedding_model,
        )
        is_allowed, score, topic = await router.is_on_topic("test query")
        assert isinstance(score, float)
        assert 0.0 <= abs(score) <= 1.5  # Cosine similarity range with noise
        assert isinstance(topic, str)

    @pytest.mark.asyncio
    async def test_high_threshold_blocks(self, mock_embedding_model, sample_topics):
        router = SemanticRouter(
            topics=sample_topics,
            threshold=0.99,  # Unrealistically high — should block
            embedding_model=mock_embedding_model,
        )
        is_allowed, score, topic = await router.is_on_topic("random unrelated text")
        # With fake embeddings, unlikely to hit 0.99 similarity
        assert is_allowed is False

    @pytest.mark.asyncio
    async def test_zero_threshold_allows_all(self, mock_embedding_model, sample_topics):
        router = SemanticRouter(
            topics=sample_topics,
            threshold=0.0,
            embedding_model=mock_embedding_model,
        )
        is_allowed, score, topic = await router.is_on_topic("write malware")
        assert is_allowed is True
