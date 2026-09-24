"""Scores for one method configuration on the test set."""

from dataclasses import dataclass
from decimal import Decimal

from app.domain.benchmark_method import BenchmarkMethod


@dataclass(frozen=True, slots=True)
class MethodResult:
    """Accuracy, latency and cost of one method at one examples-per-label setting.

    `examples_per_label` is 0 for methods that use descriptions only (A and B).
    `seed` identifies which random draw of past examples method C used; None otherwise.
    `list_price_cost_usd` is what the run would cost at list price, even on a free route.
    """

    method: BenchmarkMethod
    examples_per_label: int
    seed: int | None
    correct: int
    total: int
    accuracy: float
    accuracy_ci_low: float
    accuracy_ci_high: float
    median_latency_ms: float
    p95_latency_ms: float
    input_tokens: int
    list_price_cost_usd: Decimal
