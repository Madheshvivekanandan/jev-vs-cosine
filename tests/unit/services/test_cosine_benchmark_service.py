import itertools

from app.domain.benchmark_method import BenchmarkMethod
from app.domain.experiment_design import ExperimentDesign
from app.domain.intent_catalog import IntentCatalog
from app.domain.method_run import MethodRun
from app.services.cosine_benchmark_service import CosineBenchmarkService
from tests.conftest import KeywordEmbedder, make_messages

_DESIGN = ExperimentDesign(
    test_messages_per_label=2,
    examples_per_label_grid=(1, 3),
    example_pool_seeds=(1, 2),
    top_k_neighbours=2,
)


def _run(catalog: IntentCatalog) -> list[MethodRun]:
    ticks = itertools.count()
    service = CosineBenchmarkService(
        KeywordEmbedder(["alpha", "beta"]), _DESIGN, clock=lambda: float(next(ticks))
    )
    test_set = make_messages("alpha_intent", 2) + make_messages("beta_intent", 2)
    train_set = make_messages("alpha_intent", 4) + make_messages("beta_intent", 4)
    return service.run(catalog, test_set, train_set)


def test_run_returns_method_a_then_c_for_every_seed_and_size(catalog: IntentCatalog) -> None:
    runs = _run(catalog)

    assert runs[0].result.method is BenchmarkMethod.COSINE_DESCRIPTIONS
    assert [(r.result.seed, r.result.examples_per_label) for r in runs[1:]] == [
        (1, 1),
        (1, 3),
        (2, 1),
        (2, 3),
    ]


def test_run_classifies_separable_messages_perfectly(catalog: IntentCatalog) -> None:
    runs = _run(catalog)

    assert all(run.result.accuracy == 1.0 for run in runs)
    assert all(run.result.list_price_cost_usd == 0 for run in runs)


def test_run_reports_per_message_latency_from_the_clock(catalog: IntentCatalog) -> None:
    runs = _run(catalog)

    # The fake clock advances 1 s per reading, so each embed takes 1,000 ms.
    assert all(p.latency_ms >= 1000 for p in runs[0].predictions)
