"""Similarity strategy based on vector embeddings."""

from __future__ import annotations

import numpy as np

from backend.database.historical_models import HistoricalEvent
from backend.repositories.embedding_repository import EmbeddingRepository
from backend.services.similarity.base import SimilarityStrategy


class EmbeddingSimilarityStrategy(SimilarityStrategy):
    """Calculates similarity based on the cosine distance of event embeddings."""

    def __init__(self, embedding_repo: EmbeddingRepository):
        self._embedding_repo = embedding_repo

    @property
    def name(self) -> str:
        return "embedding"

    async def calculate(
        self,
        query_event: HistoricalEvent,
        candidates: list[HistoricalEvent],
    ) -> list[tuple[int, float]]:
        query_vector = await self._embedding_repo.get_embedding(query_event.id)
        if query_vector is None:
            return []

        scores = []
        for candidate in candidates:
            if candidate.id == query_event.id:
                continue

            candidate_vector = await self._embedding_repo.get_embedding(candidate.id)
            if candidate_vector is not None:
                score = self._cosine_similarity(query_vector, candidate_vector)
                scores.append((candidate.id, score))

        return scores

    def _cosine_similarity(self, vec_a: np.ndarray, vec_b: np.ndarray) -> float:
        """Calculates the cosine similarity between two vectors."""
        dot_product = np.dot(vec_a, vec_b)
        norm_a = np.linalg.norm(vec_a)
        norm_b = np.linalg.norm(vec_b)
        similarity = dot_product / (norm_a * norm_b)
        # Clamp the value between 0 and 1
        return max(0.0, min(1.0, similarity))