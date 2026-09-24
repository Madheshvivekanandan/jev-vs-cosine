"""Port for turning text into embedding vectors."""

from collections.abc import Sequence
from typing import Protocol

from app.services.vector_types import FloatMatrix


class Embedder(Protocol):
    """Anything that maps texts to one embedding row each, in the same order."""

    def embed(self, texts: Sequence[str]) -> FloatMatrix:
        """Return a (len(texts), dimensions) matrix of embeddings."""
        ...
