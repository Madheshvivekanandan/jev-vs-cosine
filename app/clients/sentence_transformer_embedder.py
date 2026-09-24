"""Adapter from sentence-transformers to the Embedder port (runs locally, free)."""

from collections.abc import Callable, Sequence
from functools import partial
from typing import Final

import numpy as np
from sentence_transformers import SentenceTransformer

from app.services.vector_types import FloatMatrix

# CPU keeps latency numbers comparable across machines and to a typical small server.
_DEVICE: Final = "cpu"

type EncodeFunction = Callable[[list[str]], object]


class SentenceTransformerEmbedder:
    """Embeds texts with a pinned sentence-transformers model, L2-normalised."""

    def __init__(self, encode: EncodeFunction) -> None:
        """Wrap an encode function that maps a list of texts to an array-like of vectors."""
        self._encode = encode

    def embed(self, texts: Sequence[str]) -> FloatMatrix:
        """Return one float32 embedding row per text.

        Raises:
            ValueError: If the model returns a different number of rows than texts.
        """
        vectors = np.asarray(self._encode(list(texts)), dtype=np.float32)
        if vectors.ndim != 2 or vectors.shape[0] != len(texts):
            raise ValueError("embedding model returned an unexpected shape")
        return vectors


def load_sentence_transformer_embedder(
    model_name: str, revision: str
) -> SentenceTransformerEmbedder:
    """Download (first time only) and load the pinned embedding model revision."""
    model = SentenceTransformer(model_name, revision=revision, device=_DEVICE)
    encode = partial(
        model.encode,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return SentenceTransformerEmbedder(encode)
