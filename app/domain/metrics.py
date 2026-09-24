"""Pure scoring functions: accuracy with a confidence interval, latency, cost."""

import math
import statistics
from collections.abc import Sequence
from decimal import Decimal

from app.domain.benchmark_method import BenchmarkMethod
from app.domain.method_result import MethodResult
from app.domain.prediction import Prediction

_Z_95 = 1.96
_TOKENS_PER_MILLION = Decimal(1_000_000)


def wilson_interval(correct: int, total: int, *, z: float = _Z_95) -> tuple[float, float]:
    """Return the Wilson score interval for an accuracy of `correct` out of `total`.

    Wilson stays inside [0, 1] and behaves well near 0% and 100%, unlike the normal
    approximation, which matters when comparing methods a few points apart.
    """
    if total <= 0:
        raise ValueError("total must be positive")
    rate = correct / total
    z_squared = z * z
    denominator = 1 + z_squared / total
    centre = (rate + z_squared / (2 * total)) / denominator
    margin = z * math.sqrt(rate * (1 - rate) / total + z_squared / (4 * total * total))
    # Clamp: at 0% or 100% the bound is mathematically exact but floats land at ±1e-17.
    low = max(0.0, centre - margin / denominator)
    high = min(1.0, centre + margin / denominator)
    return low, high


def nearest_rank_percentile(values: Sequence[float], fraction: float) -> float:
    """Return the nearest-rank percentile (e.g. fraction=0.95 for p95)."""
    if not values:
        raise ValueError("values must not be empty")
    ordered = sorted(values)
    rank = max(1, math.ceil(fraction * len(ordered)))
    return ordered[rank - 1]


def summarize(
    method: BenchmarkMethod,
    predictions: Sequence[Prediction],
    *,
    examples_per_label: int,
    seed: int | None,
    price_usd_per_million_tokens: Decimal,
) -> MethodResult:
    """Score one method configuration from its predictions."""
    if not predictions:
        raise ValueError("predictions must not be empty")
    correct = sum(1 for prediction in predictions if prediction.is_correct)
    total = len(predictions)
    low, high = wilson_interval(correct, total)
    latencies = [prediction.latency_ms for prediction in predictions]
    input_tokens = sum(prediction.input_tokens for prediction in predictions)
    return MethodResult(
        method=method,
        examples_per_label=examples_per_label,
        seed=seed,
        correct=correct,
        total=total,
        accuracy=correct / total,
        accuracy_ci_low=low,
        accuracy_ci_high=high,
        median_latency_ms=statistics.median(latencies),
        p95_latency_ms=nearest_rank_percentile(latencies, 0.95),
        input_tokens=input_tokens,
        list_price_cost_usd=Decimal(input_tokens)
        * price_usd_per_million_tokens
        / _TOKENS_PER_MILLION,
    )
