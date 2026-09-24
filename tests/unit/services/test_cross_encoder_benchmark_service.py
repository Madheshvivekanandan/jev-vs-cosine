import itertools
from collections.abc import Sequence

from app.domain.benchmark_method import BenchmarkMethod
from app.domain.intent_catalog import IntentCatalog
from app.services.cross_encoder_benchmark_service import CrossEncoderBenchmarkService
from tests.conftest import make_messages


class _KeywordPairScorer:
    """Scores a pair 1.0 when the document's keyword is in the query, else 0.0."""

    def __init__(self) -> None:
        self.calls: list[list[tuple[str, str]]] = []

    def score(self, pairs: Sequence[tuple[str, str]]) -> list[float]:
        self.calls.append(list(pairs))
        return [float(document.split()[0] in query) for query, document in pairs]


def _service(scorer: _KeywordPairScorer) -> CrossEncoderBenchmarkService:
    ticks = itertools.count()
    return CrossEncoderBenchmarkService(scorer, clock=lambda: float(next(ticks)) / 10)


def test_run_scores_every_category_for_every_message(catalog: IntentCatalog) -> None:
    scorer = _KeywordPairScorer()
    test_set = make_messages("alpha_intent", 2) + make_messages("beta_intent", 1)

    run = _service(scorer).run(catalog, test_set)

    assert run.result.method is BenchmarkMethod.CROSS_ENCODER_DESCRIPTIONS
    assert run.result.accuracy == 1.0
    assert all(len(pairs) == len(catalog.labels) for pairs in scorer.calls)


def test_run_pairs_the_message_with_the_same_text_method_a_embeds(
    catalog: IntentCatalog,
) -> None:
    scorer = _KeywordPairScorer()

    _service(scorer).run(catalog, make_messages("alpha_intent", 1))

    documents = [document for _query, document in scorer.calls[0]]
    assert documents == [catalog.embedding_text(label) for label in catalog.labels]


def test_run_times_all_pairs_of_one_message_as_its_latency(catalog: IntentCatalog) -> None:
    run = _service(_KeywordPairScorer()).run(catalog, make_messages("alpha_intent", 1))

    # The fake clock advances 0.1 s per reading: one reading before, one after.
    assert run.predictions[0].latency_ms == 100.0


def test_ties_go_to_catalog_order(catalog: IntentCatalog) -> None:
    run = _service(_KeywordPairScorer()).run(catalog, make_messages("gamma_intent", 1))

    assert run.predictions[0].predicted_label == catalog.labels[0]
