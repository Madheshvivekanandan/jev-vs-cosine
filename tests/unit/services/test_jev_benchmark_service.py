from decimal import Decimal
from pathlib import Path

import pytest

from app.domain.errors.budget_exceeded_error import BudgetExceededError
from app.domain.errors.jev_unavailable_error import JevUnavailableError
from app.domain.intent_catalog import IntentCatalog
from app.domain.jev_decision import JevDecision
from app.repositories.jev_decision_cache_repository import JevDecisionCacheRepository
from app.services.call_pacer import CallPacer
from app.services.jev_benchmark_service import JevBenchmarkService, cache_key
from app.services.token_budget import TokenBudget
from tests.conftest import KeywordDecider, make_messages


def _service(
    tmp_path: Path, decider: KeywordDecider, *, limit_tokens: int = 10_000
) -> tuple[JevBenchmarkService, JevDecisionCacheRepository, TokenBudget]:
    cache = JevDecisionCacheRepository(tmp_path / "cache.jsonl")
    budget = TokenBudget(limit_tokens, spent_tokens=cache.total_input_tokens())
    pacer = CallPacer(0.0, clock=lambda: 0.0, sleep=lambda _seconds: None)
    return JevBenchmarkService(decider, cache, budget, pacer), cache, budget


def test_run_predicts_every_message_and_records_tokens(
    tmp_path: Path, catalog: IntentCatalog
) -> None:
    decider = KeywordDecider(input_tokens=100)
    service, _cache, budget = _service(tmp_path, decider)
    test_set = make_messages("alpha_intent", 2) + make_messages("beta_intent", 1)

    predictions = service.run(catalog, test_set, route_id="host/m")

    assert [p.is_correct for p in predictions] == [True, True, True]
    assert budget.spent_tokens == 300


def test_run_second_time_uses_cache_and_makes_no_calls(
    tmp_path: Path, catalog: IntentCatalog
) -> None:
    test_set = make_messages("alpha_intent", 2)
    first_decider = KeywordDecider()
    _service(tmp_path, first_decider)[0].run(catalog, test_set, route_id="host/m")
    second_decider = KeywordDecider()

    _service(tmp_path, second_decider)[0].run(catalog, test_set, route_id="host/m")

    assert len(first_decider.calls) == 2
    assert second_decider.calls == []


def test_run_stops_before_the_call_that_would_break_the_budget(
    tmp_path: Path, catalog: IntentCatalog
) -> None:
    decider = KeywordDecider(input_tokens=1000)
    service, cache, _budget = _service(tmp_path, decider, limit_tokens=1500)
    test_set = make_messages("alpha_intent", 3)

    with pytest.raises(BudgetExceededError):
        service.run(catalog, test_set, route_id="host/m")

    assert len(decider.calls) == 1
    assert cache.get(cache_key("host/m", catalog, test_set[0].text)) is not None


def test_run_when_usage_missing_charges_the_estimate(
    tmp_path: Path, catalog: IntentCatalog
) -> None:
    decider = KeywordDecider(input_tokens=None)
    service, _cache, budget = _service(tmp_path, decider)

    service.run(catalog, make_messages("alpha_intent", 1), route_id="host/m")

    assert budget.spent_tokens > 0


def test_run_keeps_earlier_answers_when_jev_becomes_unavailable(
    tmp_path: Path, catalog: IntentCatalog
) -> None:
    class _FailsOnSecondCall(KeywordDecider):
        def decide(self, message: str, catalog: IntentCatalog) -> JevDecision:
            if self.calls:
                raise JevUnavailableError("rate limited")
            return super().decide(message, catalog)

    service, cache, _budget = _service(tmp_path, _FailsOnSecondCall())
    test_set = make_messages("alpha_intent", 2)

    with pytest.raises(JevUnavailableError):
        service.run(catalog, test_set, route_id="host/m")

    assert cache.get(cache_key("host/m", catalog, test_set[0].text)) is not None


def test_estimate_counts_only_uncached_messages(tmp_path: Path, catalog: IntentCatalog) -> None:
    test_set = make_messages("alpha_intent", 3)
    service, _cache, _budget = _service(tmp_path, KeywordDecider(input_tokens=2000))
    service.run(catalog, test_set[:1], route_id="host/m")

    estimate = service.estimate(
        catalog, test_set, route_id="host/m", price_usd_per_million_tokens=Decimal("0.042")
    )

    assert (estimate.cached_messages, estimate.uncached_messages) == (1, 2)
    assert estimate.estimated_tokens == 2 * 2200  # observed average plus a 10% margin
    assert estimate.fits_budget


def test_estimate_before_any_usage_uses_character_heuristic(
    tmp_path: Path, catalog: IntentCatalog
) -> None:
    service, _cache, _budget = _service(tmp_path, KeywordDecider())

    estimate = service.estimate(
        catalog,
        make_messages("alpha_intent", 1),
        route_id="host/m",
        price_usd_per_million_tokens=Decimal("0.042"),
    )

    assert estimate.estimated_tokens > 350


def test_cache_key_depends_on_model_catalog_and_text(catalog: IntentCatalog) -> None:
    base = cache_key("host/m", catalog, "hello")

    assert base == cache_key("host/m", catalog, "hello")
    assert base != cache_key("host/other", catalog, "hello")
    assert base != cache_key("host/m", catalog, "hello!")


def test_served_models_lists_models_reported_for_cached_answers(
    tmp_path: Path, catalog: IntentCatalog
) -> None:
    service, _cache, _budget = _service(tmp_path, KeywordDecider())
    test_set = make_messages("alpha_intent", 2)
    service.run(catalog, test_set[:1], route_id="host/m")

    assert service.served_models(catalog, test_set, route_id="host/m") == ["fake-jev"]


def test_missing_usage_is_charged_as_the_estimate_in_predictions(
    tmp_path: Path, catalog: IntentCatalog
) -> None:
    service, cache, budget = _service(tmp_path, KeywordDecider(input_tokens=None))

    predictions = service.run(catalog, make_messages("alpha_intent", 1), route_id="host/m")

    assert predictions[0].input_tokens == budget.spent_tokens > 0
    assert cache.total_input_tokens() == budget.spent_tokens


def test_estimate_uses_catalog_size_when_it_exceeds_the_observed_average(
    tmp_path: Path, catalog: IntentCatalog
) -> None:
    service, _cache, _budget = _service(tmp_path, KeywordDecider(input_tokens=10))
    service.run(catalog, make_messages("alpha_intent", 1), route_id="host/m")
    big = IntentCatalog(version="big", instructions="q", descriptions={"alpha_intent": "x" * 4000})

    estimate = service.estimate(
        big,
        make_messages("alpha_intent", 1),
        route_id="host/m",
        price_usd_per_million_tokens=Decimal(0),
    )

    assert estimate.estimated_tokens > 1000
