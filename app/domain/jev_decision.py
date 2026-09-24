"""Jev's answer to one intent question."""

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class JevDecision:
    """The chosen intent with Jev's probabilities and the call's usage.

    `input_tokens` is None when the route did not report usage; the budget then
    falls back to the pre-flight estimate.
    """

    choice: str
    confidence: float
    probabilities: Mapping[str, float]
    input_tokens: int | None
    model: str
    latency_ms: float
