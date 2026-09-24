"""Embed test messages one at a time, timing each, for methods that start from embeddings."""

from collections.abc import Callable, Sequence
from dataclasses import dataclass

import numpy as np

from app.domain.labeled_message import LabeledMessage
from app.services.ports.embedder import Embedder
from app.services.vector_types import FloatMatrix


@dataclass(frozen=True, slots=True)
class EmbeddedMessages:
    """Messages with their embeddings and the time each embedding took."""

    messages: Sequence[LabeledMessage]
    vectors: FloatMatrix
    embed_latencies_ms: Sequence[float]


def embed_one_at_a_time(
    embedder: Embedder, messages: Sequence[LabeledMessage], clock: Callable[[], float]
) -> EmbeddedMessages:
    """Embed each message separately, so per-message latency is what a live system sees."""
    rows: list[FloatMatrix] = []
    latencies_ms: list[float] = []
    for message in messages:
        started = clock()
        rows.append(embedder.embed([message.text]))
        latencies_ms.append((clock() - started) * 1000)
    return EmbeddedMessages(messages, np.vstack(rows).astype(np.float32), latencies_ms)
