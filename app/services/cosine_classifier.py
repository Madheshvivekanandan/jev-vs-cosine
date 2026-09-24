"""Cosine similarity plus top-k voting: the whole of methods A and C.

Method A is top-1 against one description per label; method C is a similarity-
weighted top-k vote against individual past examples. Same maths, different
reference texts.
"""

import math
from collections.abc import Sequence

import numpy as np

from app.services.vector_types import FloatMatrix


def normalize_rows(vectors: FloatMatrix) -> FloatMatrix:
    """Return each row scaled to unit length.

    Raises:
        ValueError: If any row is all zeros, since it has no direction to compare.
    """
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    if np.any(norms == 0):
        raise ValueError("cannot normalise a zero vector")
    return (vectors / norms).astype(np.float32)


def cosine_similarities(queries: FloatMatrix, references: FloatMatrix) -> FloatMatrix:
    """Return a (queries, references) matrix of cosine similarities."""
    return normalize_rows(queries) @ normalize_rows(references).T


def vote_top_k(similarities: FloatMatrix, reference_labels: Sequence[str], *, k: int) -> list[str]:
    """Return one label per query row by a similarity-weighted vote of its top-k references.

    Each of the k most similar references adds its similarity to its label's score and
    the highest score wins. A tie goes to the label of the single most similar reference.
    With k=1 this is plain nearest-neighbour.
    """
    if similarities.shape[1] != len(reference_labels):
        raise ValueError("need exactly one label per reference column")
    if k < 1:
        raise ValueError("k must be at least 1")
    top_k = min(k, len(reference_labels))
    return [
        _vote_row(similarities[row], reference_labels, top_k)
        for row in range(similarities.shape[0])
    ]


def _vote_row(row: FloatMatrix, reference_labels: Sequence[str], top_k: int) -> str:
    ranked = [int(index) for index in np.argsort(-row, kind="stable")[:top_k]]
    scores: dict[str, float] = {}
    for index in ranked:
        label = reference_labels[index]
        scores[label] = scores.get(label, 0.0) + float(row[index])
    best_score = max(scores.values())
    return next(
        reference_labels[index]
        for index in ranked
        if math.isclose(scores[reference_labels[index]], best_score)
    )
