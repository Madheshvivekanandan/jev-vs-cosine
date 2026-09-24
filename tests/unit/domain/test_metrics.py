from decimal import Decimal

import pytest

from app.domain.benchmark_method import BenchmarkMethod
from app.domain.metrics import nearest_rank_percentile, summarize, wilson_interval
from app.domain.prediction import Prediction


def _prediction(*, correct: bool, latency_ms: float = 10.0, tokens: int = 0) -> Prediction:
    return Prediction(
        text="t",
        true_label="a",
        predicted_label="a" if correct else "b",
        latency_ms=latency_ms,
        input_tokens=tokens,
    )


def test_wilson_interval_when_half_correct_is_symmetric_around_half() -> None:
    low, high = wilson_interval(50, 100)

    assert low == pytest.approx(0.4038, abs=1e-3)
    assert high == pytest.approx(0.5962, abs=1e-3)


@pytest.mark.parametrize(("correct", "total"), [(0, 10), (10, 10)])
def test_wilson_interval_at_extremes_stays_within_unit_range(correct: int, total: int) -> None:
    low, high = wilson_interval(correct, total)

    assert 0.0 <= low <= high <= 1.0


def test_wilson_interval_when_total_is_zero_raises() -> None:
    with pytest.raises(ValueError, match="positive"):
        wilson_interval(0, 0)


def test_nearest_rank_percentile_returns_p95_value() -> None:
    values = [float(v) for v in range(1, 101)]

    assert nearest_rank_percentile(values, 0.95) == 95.0


def test_nearest_rank_percentile_when_empty_raises() -> None:
    with pytest.raises(ValueError, match="empty"):
        nearest_rank_percentile([], 0.5)


def test_summarize_computes_accuracy_latency_and_decimal_cost() -> None:
    predictions = [
        _prediction(correct=True, latency_ms=10, tokens=1_000_000),
        _prediction(correct=True, latency_ms=20, tokens=1_000_000),
        _prediction(correct=False, latency_ms=30, tokens=0),
        _prediction(correct=True, latency_ms=40, tokens=0),
    ]

    result = summarize(
        BenchmarkMethod.JEV,
        predictions,
        examples_per_label=0,
        seed=None,
        price_usd_per_million_tokens=Decimal("0.042"),
    )

    assert (result.correct, result.total, result.accuracy) == (3, 4, 0.75)
    assert result.median_latency_ms == 25.0
    assert result.p95_latency_ms == 40.0
    assert result.input_tokens == 2_000_000
    assert result.list_price_cost_usd == Decimal("0.084")


def test_summarize_when_no_predictions_raises() -> None:
    with pytest.raises(ValueError, match="empty"):
        summarize(
            BenchmarkMethod.JEV,
            [],
            examples_per_label=0,
            seed=None,
            price_usd_per_million_tokens=Decimal(0),
        )
