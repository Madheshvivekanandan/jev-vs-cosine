import numpy as np
import pytest

from app.services.cosine_classifier import cosine_similarities, normalize_rows, vote_top_k
from app.services.vector_types import FloatMatrix


def _matrix(rows: list[list[float]]) -> FloatMatrix:
    return np.array(rows, dtype=np.float32)


def test_cosine_similarities_ignores_vector_length() -> None:
    queries = _matrix([[2.0, 0.0]])
    references = _matrix([[5.0, 0.0], [0.0, 3.0]])

    similarities = cosine_similarities(queries, references)

    assert similarities[0].tolist() == pytest.approx([1.0, 0.0])


def test_normalize_rows_with_zero_vector_raises() -> None:
    with pytest.raises(ValueError, match="zero"):
        normalize_rows(_matrix([[0.0, 0.0]]))


def test_vote_top_k_with_k1_is_nearest_neighbour() -> None:
    similarities = _matrix([[0.2, 0.9, 0.5]])

    assert vote_top_k(similarities, ["a", "b", "c"], k=1) == ["b"]


def test_vote_top_k_sums_similarity_per_label() -> None:
    # "b" has the single best neighbour, but two "a" neighbours outweigh it.
    similarities = _matrix([[0.8, 0.7, 0.9]])

    assert vote_top_k(similarities, ["a", "a", "b"], k=3) == ["a"]


def test_vote_top_k_tie_goes_to_label_of_most_similar_reference() -> None:
    similarities = _matrix([[0.5, 0.5, 1.0, 0.0]])

    assert vote_top_k(similarities, ["a", "a", "b", "c"], k=3) == ["b"]


def test_vote_top_k_clamps_k_to_reference_count() -> None:
    similarities = _matrix([[0.1, 0.9]])

    assert vote_top_k(similarities, ["a", "b"], k=50) == ["b"]


@pytest.mark.parametrize(("labels", "k"), [(["a"], 1), (["a", "b"], 0)])
def test_vote_top_k_rejects_bad_arguments(labels: list[str], k: int) -> None:
    with pytest.raises(ValueError):
        vote_top_k(_matrix([[0.1, 0.9]]), labels, k=k)
