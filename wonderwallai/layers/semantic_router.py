"""
WonderwallAi — Semantic Router Layer
Enforces topic boundaries using cosine similarity of sentence embeddings.
Off-topic messages are blocked before they reach the LLM.
"""

import asyncio
import logging
from typing import List, Optional, Tuple

import numpy as np

logger = logging.getLogger("wonderwallai.semantic_router")


class SemanticRouter:
    """
    Topic boundary enforcement via vector embeddings.

    Args:
        topics: List of allowed topic descriptions. Empty list disables routing.
        threshold: Minimum cosine similarity to classify as on-topic.
        embedding_model: Pre-loaded SentenceTransformer (optional, avoids duplicate memory).
        model_name: Model to load if ``embedding_model`` is None and topics are provided.
    """

    def __init__(
        self,
        topics: List[str],
        threshold: float = 0.35,
        embedding_model=None,
        model_name: str = "all-MiniLM-L6-v2",
    ):
        self.topics = topics
        self.threshold = threshold
        self.embedding_model = embedding_model
        self._allowed_embeddings: Optional[np.ndarray] = None

        if not self.topics:
            logger.info("SemanticRouter: no topics configured — routing disabled")
            return

        # Load model if not injected
        if self.embedding_model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self.embedding_model = SentenceTransformer(model_name)
                logger.info(f"SemanticRouter: loaded model '{model_name}'")
            except ImportError:
                logger.warning(
                    "sentence-transformers not installed — semantic routing disabled. "
                    "Install with: pip install wonderwallai[semantic]"
                )
                return

        self._precompute_topic_embeddings()

    def _precompute_topic_embeddings(self):
        """Encode all allowed topics at init time (one-time cost, sub-second)."""
        embeddings = self.embedding_model.encode(
            self.topics, normalize_embeddings=True
        )
        self._allowed_embeddings = np.array(embeddings)
        logger.info(
            f"SemanticRouter: pre-computed {len(self.topics)} topic embeddings"
        )

    async def is_on_topic(self, query: str) -> Tuple[bool, float, str]:
        """
        Check if a query is semantically within allowed topics.

        Returns:
            Tuple of (is_allowed, max_similarity_score, closest_topic).
        """
        if self._allowed_embeddings is None:
            return (True, 1.0, "router_disabled")

        loop = asyncio.get_running_loop()
        query_embedding = await loop.run_in_executor(
            None,
            lambda: self.embedding_model.encode(
                [query], normalize_embeddings=True
            ),
        )

        # Cosine similarity (embeddings are already L2-normalized)
        similarities = np.dot(self._allowed_embeddings, query_embedding[0])
        max_idx = int(np.argmax(similarities))
        max_sim = float(similarities[max_idx])
        closest_topic = self.topics[max_idx]

        is_allowed = max_sim >= self.threshold

        if not is_allowed:
            logger.warning(
                f"SemanticRouter BLOCKED | sim={max_sim:.3f} | "
                f"closest='{closest_topic[:50]}' | query='{query[:60]}'"
            )

        return (is_allowed, max_sim, closest_topic)
