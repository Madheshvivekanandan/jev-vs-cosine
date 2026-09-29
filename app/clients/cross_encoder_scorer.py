"""Adapter from a sentence-transformers CrossEncoder (reranker) to the PairScorer port."""

from collections.abc import Callable, Sequence
from functools import partial
from typing import Final

import numpy as np
from sentence_transformers import CrossEncoder

# CPU keeps latency comparable with the cosine methods and with a typical small server.
_DEVICE: Final = "cpu"
_BATCH_SIZE: Final = 32

type PredictFunction = Callable[[list[tuple[str, str]]], object]


class CrossEncoderScorer:
    """Scores pairs with a pinned reranker, run locally."""

    def __init__(self, predict: PredictFunction) -> None:
        """Wrap a predict function that maps a list of pairs to an array-like of scores."""
        self._predict = predict

    def score(self, pairs: Sequence[tuple[str, str]]) -> list[float]:
        """Return one float score per pair.

        Raises:
            ValueError: If the model returns a different number of scores than pairs.
        """
        scores = np.asarray(self._predict(list(pairs)), dtype=np.float64).reshape(-1)
        if scores.shape[0] != len(pairs):
            raise ValueError("cross-encoder returned an unexpected number of scores")
        return [float(value) for value in scores]


def load_cross_encoder_scorer(model_name: str, revision: str) -> CrossEncoderScorer:
    """Download (first time only) and load the pinned reranker revision."""
    model = CrossEncoder(model_name, revision=revision, device=_DEVICE)
    predict = partial(
        model.predict,
        batch_size=_BATCH_SIZE,
        show_progress_bar=False,
        convert_to_numpy=True,
    )
    return CrossEncoderScorer(predict)
