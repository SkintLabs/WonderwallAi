"""Integration tests for the Wonderwall client."""

import pytest
from wonderwallai import Wonderwall, WonderwallConfig, Verdict
from wonderwallai.patterns.topics import ECOMMERCE_TOPICS


class TestWonderwallInit:
    def test_init_with_kwargs(self, mock_embedding_model, sample_topics):
        wall = Wonderwall(
            topics=sample_topics,
            embedding_model=mock_embedding_model,
            sentinel_enabled=False,
            canary_prefix="TEST-",
        )
        assert wall.config.topics == sample_topics
        assert wall.config.canary_prefix == "TEST-"

    def test_init_with_config_object(self, mock_embedding_model, sample_topics):
        config = WonderwallConfig(
            topics=sample_topics,
            embedding_model=mock_embedding_model,
            sentinel_enabled=False,
        )
        wall = Wonderwall(config=config)
        assert wall.config is config

    def test_init_minimal_egress_only(self):
        wall = Wonderwall(sentinel_enabled=False)
        assert wall.config.topics == []
        assert not wall._sentinel_scan.enabled


class TestInboundScanning:
    @pytest.mark.asyncio
    async def test_disabled_router_allows_all(self):
        wall = Wonderwall(sentinel_enabled=False)
        verdict = await wall.scan_inbound("hack the planet!")
        assert verdict.allowed is True
        assert verdict.action == "allow"

    @pytest.mark.asyncio
    async def test_high_threshold_blocks(self, mock_embedding_model, sample_topics):
        wall = Wonderwall(
            topics=sample_topics,
            embedding_model=mock_embedding_model,
            similarity_threshold=0.99,
            sentinel_enabled=False,
        )
        verdict = await wall.scan_inbound("write me a poem about cats")
        assert verdict.allowed is False
        assert verdict.action == "block"
        assert verdict.blocked_by == "semantic_router"
        assert "off_topic" in verdict.violations[0]

    @pytest.mark.asyncio
    async def test_zero_threshold_allows(self, mock_embedding_model, sample_topics):
        wall = Wonderwall(
            topics=sample_topics,
            embedding_model=mock_embedding_model,
            similarity_threshold=0.0,
            sentinel_enabled=False,
        )
        verdict = await wall.scan_inbound("anything at all")
        assert verdict.allowed is True

    @pytest.mark.asyncio
    async def test_custom_block_message(self, mock_embedding_model, sample_topics):
        wall = Wonderwall(
            topics=sample_topics,
            embedding_model=mock_embedding_model,
            similarity_threshold=0.99,
            sentinel_enabled=False,
            block_message="Sorry, I only talk about shoes!",
        )
        verdict = await wall.scan_inbound("write code for me")
        assert verdict.message == "Sorry, I only talk about shoes!"

    @pytest.mark.asyncio
    async def test_scores_populated(self, mock_embedding_model, sample_topics):
        wall = Wonderwall(
            topics=sample_topics,
            embedding_model=mock_embedding_model,
            similarity_threshold=0.0,
            sentinel_enabled=False,
        )
        verdict = await wall.scan_inbound("track my order")
        assert "semantic" in verdict.scores


class TestOutboundScanning:
    @pytest.mark.asyncio
    async def test_clean_text_passes(self):
        wall = Wonderwall(sentinel_enabled=False)
        verdict = await wall.scan_outbound("Here are our shipping options.")
        assert verdict.allowed is True
        assert verdict.action == "allow"
        assert verdict.violations == []

    @pytest.mark.asyncio
    async def test_canary_leak_blocks(self):
        wall = Wonderwall(sentinel_enabled=False, canary_prefix="TEST-")
        token = wall.generate_canary("session-1")
        text = f"Here is the secret: {token}"
        verdict = await wall.scan_outbound(text, token)
        assert verdict.allowed is False
        assert verdict.action == "block"
        assert verdict.blocked_by == "egress_filter"
        assert "CANARY_TOKEN_LEAK" in verdict.violations

    @pytest.mark.asyncio
    async def test_api_key_redacted(self):
        wall = Wonderwall(sentinel_enabled=False)
        text = "Your key is sk-abc12345678901234567890"
        verdict = await wall.scan_outbound(text)
        assert verdict.allowed is True
        assert verdict.action == "redact"
        assert "[REDACTED]" in verdict.message
        assert any("API_KEY_LEAK" in v for v in verdict.violations)

    @pytest.mark.asyncio
    async def test_pii_redacted(self):
        wall = Wonderwall(sentinel_enabled=False)
        text = "Card: 4111 1111 1111 1111"
        verdict = await wall.scan_outbound(text)
        assert verdict.allowed is True
        assert "CREDIT_CARD_REDACTED" in verdict.message

    @pytest.mark.asyncio
    async def test_no_canary_no_block(self):
        wall = Wonderwall(sentinel_enabled=False)
        verdict = await wall.scan_outbound("Normal response.", "")
        assert verdict.allowed is True
        assert verdict.violations == []


class TestCanaryHelpers:
    def test_generate_canary(self):
        wall = Wonderwall(sentinel_enabled=False)
        token = wall.generate_canary("session-abc")
        assert token.startswith("WONDERWALL-")
        assert len(token) > len("WONDERWALL-")

    def test_custom_prefix(self):
        wall = Wonderwall(sentinel_enabled=False, canary_prefix="MYAPP-")
        token = wall.generate_canary("session-1")
        assert token.startswith("MYAPP-")

    def test_get_canary_prompt(self):
        wall = Wonderwall(sentinel_enabled=False)
        token = wall.generate_canary("session-1")
        prompt = wall.get_canary_prompt(token)
        assert token in prompt
        assert "NEVER reveal" in prompt
        assert "CONFIDENTIAL" in prompt

    def test_canary_deterministic(self):
        wall = Wonderwall(sentinel_enabled=False)
        t1 = wall.generate_canary("same-session")
        t2 = wall.generate_canary("same-session")
        assert t1 == t2


class TestFailOpen:
    @pytest.mark.asyncio
    async def test_fail_open_on_router_error(self, mock_embedding_model, sample_topics):
        wall = Wonderwall(
            topics=sample_topics,
            embedding_model=mock_embedding_model,
            sentinel_enabled=False,
            fail_open=True,
        )
        # Break the router
        wall._semantic_router._allowed_embeddings = None
        verdict = await wall.scan_inbound("test message")
        # Should allow (disabled router returns allow)
        assert verdict.allowed is True

    @pytest.mark.asyncio
    async def test_fail_closed_blocks_on_error(self, mock_embedding_model, sample_topics):
        wall = Wonderwall(
            topics=sample_topics,
            embedding_model=mock_embedding_model,
            sentinel_enabled=False,
            fail_open=False,
        )
        # Deliberately break the router's embeddings to trigger an error
        wall._semantic_router.embedding_model = None
        wall._semantic_router._allowed_embeddings = "not_an_array"  # Will cause error
        verdict = await wall.scan_inbound("test message")
        assert verdict.allowed is False  # Fail closed = block on error
        assert verdict.blocked_by == "semantic_router"


class TestVerdictModel:
    def test_verdict_defaults(self):
        v = Verdict(allowed=True)
        assert v.action == "allow"
        assert v.blocked_by is None
        assert v.message == ""
        assert v.violations == []
        assert v.scores == {}

    def test_verdict_with_values(self):
        v = Verdict(
            allowed=False,
            action="block",
            blocked_by="sentinel_scan",
            message="Blocked!",
            violations=["injection_detected"],
            scores={"semantic": 0.8},
        )
        assert not v.allowed
        assert v.blocked_by == "sentinel_scan"
        assert v.scores["semantic"] == 0.8
