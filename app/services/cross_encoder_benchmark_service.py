"""Method D: a cross-encoder reads each message together with every category description."""

import logging
from collections.abc import Callable, Sequence
from decimal import Decimal

from app.domain.benchmark_method import BenchmarkMethod
from app.domain.intent_catalog import IntentCatalog
from app.domain.labeled_message import LabeledMessage
from app.domain.method_run import MethodRun
from app.domain.metrics import summarize
from app.domain.prediction import Prediction
from app.services.ports.pair_scorer import PairScorer

logger = logging.getLogger(__name__)

_FREE = Decimal(0)


class CrossEncoderBenchmarkService:
    """Scores (message, "name: description") for every category and picks the best.

    It uses exactly the text method A embeds, with no examples, so the only difference
    from A is reading the message and each description together instead of apart. Each
    message costs one pass per category (77 pairs), and all of it is timed as latency.
    """

    def __init__(self, scorer: PairScorer, *, clock: Callable[[], float]) -> None:
        """Wire the service to a pair scorer and a clock."""
        self._scorer = scorer
        self._clock = clock

    def run(self, catalog: IntentCatalog, test_set: Sequence[LabeledMessage]) -> MethodRun:
        """Return method D's run over the test set."""
        labels = catalog.labels
        documents = [catalog.embedding_text(label) for label in labels]
        predictions = tuple(self._predict(message, labels, documents) for message in test_set)
        result = summarize(
            BenchmarkMethod.CROSS_ENCODER_DESCRIPTIONS,
            predictions,
            examples_per_label=0,
            seed=None,
            price_usd_per_million_tokens=_FREE,
        )
        logger.info("cross_encoder_run_complete", extra={"messages": len(predictions)})
        return MethodRun(result, predictions)

    def _predict(
        self, message: LabeledMessage, labels: Sequence[str], documents: Sequence[str]
    ) -> Prediction:
        started = self._clock()
        scores = self._scorer.score([(message.text, document) for document in documents])
        latency_ms = (self._clock() - started) * 1000
        # max() keeps the first of equal scores, so ties go to catalog order.
        best = max(range(len(labels)), key=scores.__getitem__)
        return Prediction(
            text=message.text,
            true_label=message.label,
            predicted_label=labels[best],
            latency_ms=latency_ms,
        )
