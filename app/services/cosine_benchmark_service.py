"""Methods A and C: cosine similarity against descriptions, then against past examples."""

import logging
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from decimal import Decimal

import numpy as np

from app.domain.benchmark_method import BenchmarkMethod
from app.domain.experiment_design import ExperimentDesign
from app.domain.intent_catalog import IntentCatalog
from app.domain.labeled_message import LabeledMessage
from app.domain.method_run import MethodRun
from app.domain.metrics import summarize
from app.domain.prediction import Prediction
from app.services.cosine_classifier import cosine_similarities, vote_top_k
from app.services.embedded_messages import EmbeddedMessages, embed_one_at_a_time
from app.services.ports.embedder import Embedder
from app.services.sampling import draw_example_pools, take_examples
from app.services.vector_types import FloatMatrix

logger = logging.getLogger(__name__)

_FREE = Decimal(0)


@dataclass(frozen=True, slots=True)
class _ReferenceSet:
    """What the test messages are compared against, and how the vote is configured."""

    method: BenchmarkMethod
    vectors: FloatMatrix
    labels: Sequence[str]
    examples_per_label: int
    seed: int | None
    top_k: int


class CosineBenchmarkService:
    """Runs method A once and method C for every (seed, examples-per-label) pair.

    Test messages are embedded one at a time so the per-message latency is what a live
    system would see. Reference texts (descriptions, past examples) are embedded in
    batches up front, as a live system would precompute them, so they are not timed.
    """

    def __init__(
        self, embedder: Embedder, design: ExperimentDesign, *, clock: Callable[[], float]
    ) -> None:
        """Wire the service to an embedding model, the experiment design and a clock."""
        self._embedder = embedder
        self._design = design
        self._clock = clock

    def run(
        self,
        catalog: IntentCatalog,
        test_set: Sequence[LabeledMessage],
        train_set: Sequence[LabeledMessage],
    ) -> list[MethodRun]:
        """Return method A's run followed by every method C run.

        Raises:
            DatasetError: If a training label has too few examples for the design.
        """
        embedded = embed_one_at_a_time(self._embedder, test_set, self._clock)
        runs = [self._run_against_descriptions(catalog, embedded)]
        for seed in self._design.example_pool_seeds:
            runs.extend(self._run_against_examples(train_set, embedded, seed))
        logger.info("cosine_runs_complete", extra={"runs": len(runs)})
        return runs

    def _run_against_descriptions(
        self, catalog: IntentCatalog, embedded: EmbeddedMessages
    ) -> MethodRun:
        labels = list(catalog.labels)
        vectors = self._embedder.embed([catalog.embedding_text(label) for label in labels])
        references = _ReferenceSet(
            BenchmarkMethod.COSINE_DESCRIPTIONS, vectors, labels, 0, None, top_k=1
        )
        return self._classify(embedded, references)

    def _run_against_examples(
        self, train_set: Sequence[LabeledMessage], embedded: EmbeddedMessages, seed: int
    ) -> list[MethodRun]:
        largest = self._design.max_examples_per_label
        pools = draw_example_pools(train_set, max_per_label=largest, seed=seed)
        pool_messages = take_examples(pools, largest)
        pool_vectors = self._embedder.embed([message.text for message in pool_messages])
        ranks = np.array([rank for label in sorted(pools) for rank in range(largest)])
        runs: list[MethodRun] = []
        for per_label in self._design.examples_per_label_grid:
            kept = ranks < per_label
            labels = [m.label for m, keep in zip(pool_messages, kept, strict=True) if keep]
            references = _ReferenceSet(
                BenchmarkMethod.COSINE_EXAMPLES,
                pool_vectors[kept],
                labels,
                per_label,
                seed,
                top_k=self._design.top_k_neighbours,
            )
            runs.append(self._classify(embedded, references))
        return runs

    def _classify(self, embedded: EmbeddedMessages, references: _ReferenceSet) -> MethodRun:
        started = self._clock()
        similarities = cosine_similarities(embedded.vectors, references.vectors)
        guesses = vote_top_k(similarities, references.labels, k=references.top_k)
        scoring_ms = (self._clock() - started) * 1000 / len(embedded.messages)
        predictions = tuple(
            Prediction(
                text=message.text,
                true_label=message.label,
                predicted_label=guess,
                latency_ms=embed_ms + scoring_ms,
            )
            for message, guess, embed_ms in zip(
                embedded.messages, guesses, embedded.embed_latencies_ms, strict=True
            )
        )
        result = summarize(
            references.method,
            predictions,
            examples_per_label=references.examples_per_label,
            seed=references.seed,
            price_usd_per_million_tokens=_FREE,
        )
        return MethodRun(result, predictions)
