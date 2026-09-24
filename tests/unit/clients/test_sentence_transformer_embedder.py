import numpy as np
import pytest

from app.clients.sentence_transformer_embedder import SentenceTransformerEmbedder


def test_embed_returns_float32_rows_in_input_order() -> None:
    embedder = SentenceTransformerEmbedder(lambda texts: [[float(len(t)), 1.0] for t in texts])

    vectors = embedder.embed(["a", "abc"])

    assert vectors.dtype == np.float32
    assert vectors[:, 0].tolist() == [1.0, 3.0]


def test_embed_when_model_returns_wrong_row_count_raises() -> None:
    embedder = SentenceTransformerEmbedder(lambda _texts: [[1.0, 2.0]])

    with pytest.raises(ValueError, match="unexpected shape"):
        embedder.embed(["a", "b"])
