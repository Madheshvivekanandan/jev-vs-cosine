"""Method E: train a classifier on the same past examples method C votes with."""

import logging
from collections.abc import Callable, Sequence
from decimal import Decimal

import numpy as np

from app.domain.benchmark_method import BenchmarkMethod
from app.domain.experiment_design import ExperimentDesign
from app.domain.labeled_message import LabeledMessage
from app.domain.method_run import MethodRun
from app.domain.metrics import summarize
from app.domain.prediction import Prediction
from app.services.embedded_messages import EmbeddedMessages, embed_one_at_a_time
from app.services.ports.classifier_trainer import ClassifierTrainer
from app.services.ports.embedder import Embedder
from app.services.ports.fitted_classifier import FittedClassifier
from app.services.sampling import draw_example_pools, take_examples

logger = logging.getLogger(__name__)

_FREE = Decimal(0)


class TrainedClassifierBenchmarkService:
    """Runs method E for every (seed, examples-per-label) pair in the design.

    The example pools come from the same seeded draw as method C, so C and E see
    identical past messages and differ only in how they use them: a top-k vote versus a
    trained classifier. Training is offline and untimed; latency is embedding plus
    prediction per message, as a live system would pay.
    """

    def __init__(
        self,
        embedder: Embedder,
        trainer: ClassifierTrainer,
        design: ExperimentDesign,
        *,
        clock: Callable[[], float],
    ) -> None:
        """Wire the service to an embedder, a trainer, the design and a clock."""
        self._embedder = embedder
        self._trainer = trainer
        self._design = design
        self._clock = clock

    def run(
        self, test_set: Sequence[LabeledMessage], train_set: Sequence[LabeledMessage]
    ) -> list[MethodRun]:
        """Return one method E run per (seed, examples-per-label) pair.

        Raises:
            DatasetError: If a training label has too few examples for the design.
        """
        embedded = embed_one_at_a_time(self._embedder, test_set, self._clock)
        runs: list[MethodRun] = []
        for seed in self._design.example_pool_seeds:
            runs.extend(self._run_seed(train_set, embedded, seed))
        logger.info("trained_classifier_runs_complete", extra={"runs": len(runs)})
        return runs

    def _run_seed(
        self, train_set: Sequence[LabeledMessage], embedded: EmbeddedMessages, seed: int
    ) -> list[MethodRun]:
        largest = self._design.max_examples_per_label
        pools = draw_example_pools(train_set, max_per_label=largest, seed=seed)
        pool_messages = take_examples(pools, largest)
        pool_vectors = self._embedder.embed([message.text for message in pool_messages])
        ranks = np.array([rank for _label in sorted(pools) for rank in range(largest)])
        runs: list[MethodRun] = []
        for per_label in self._design.examples_per_label_grid:
            kept = ranks < per_label
            labels = [m.label for m, keep in zip(pool_messages, kept, strict=True) if keep]
            classifier = self._trainer.fit(pool_vectors[kept], labels)
            runs.append(self._evaluate(classifier, embedded, per_label, seed))
        return runs

    def _evaluate(
        self, classifier: FittedClassifier, embedded: EmbeddedMessages, per_label: int, seed: int
    ) -> MethodRun:
        started = self._clock()
        guesses = classifier.predict(embedded.vectors)
        predict_ms = (self._clock() - started) * 1000 / len(embedded.messages)
        predictions = tuple(
            Prediction(
                text=message.text,
                true_label=message.label,
                predicted_label=guess,
                latency_ms=embed_ms + predict_ms,
            )
            for message, guess, embed_ms in zip(
                embedded.messages, guesses, embedded.embed_latencies_ms, strict=True
            )
        )
        result = summarize(
            BenchmarkMethod.TRAINED_CLASSIFIER,
            predictions,
            examples_per_label=per_label,
            seed=seed,
            price_usd_per_million_tokens=_FREE,
        )
        return MethodRun(result, predictions)
