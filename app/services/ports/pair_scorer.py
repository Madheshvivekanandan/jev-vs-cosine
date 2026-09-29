"""Port for scoring (query, document) text pairs jointly."""

from collections.abc import Sequence
from typing import Protocol


class PairScorer(Protocol):
    """Anything that reads each (query, document) pair together and returns a relevance score.

    Unlike an Embedder, which encodes each text on its own, a pair scorer sees both texts
    at once, so it can react to negation or to which part of the message matters.
    """

    def score(self, pairs: Sequence[tuple[str, str]]) -> list[float]:
        """Return one score per pair, in order; higher means more relevant."""
        ...
