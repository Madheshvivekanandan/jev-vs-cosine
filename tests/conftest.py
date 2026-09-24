"""Shared factories and fakes. Fakes implement the app's Protocols; nothing hits a network."""

import logging
from collections.abc import Iterator, Sequence
from decimal import Decimal

import numpy as np
import pytest

from app.domain.benchmark_method import BenchmarkMethod
from app.domain.intent_catalog import IntentCatalog
from app.domain.jev_decision import JevDecision
from app.domain.labeled_message import LabeledMessage
from app.domain.method_result import MethodResult
from app.services.vector_types import FloatMatrix


def make_catalog(labels: Sequence[str] = ("alpha_intent", "beta_intent")) -> IntentCatalog:
    """Return a small catalog whose descriptions mention each label's keyword."""
    return IntentCatalog(
        version="test.v1",
        instructions="Which intent?",
        descriptions={label: f"about {label.split('_')[0]}" for label in labels},
    )


def make_messages(label: str, count: int, keyword: str | None = None) -> list[LabeledMessage]:
    """Return `count` messages for `label`, each containing its keyword."""
    word = keyword or label.split("_")[0]
    return [LabeledMessage(text=f"{word} message {index}", label=label) for index in range(count)]


def make_result(
    method: BenchmarkMethod = BenchmarkMethod.COSINE_EXAMPLES,
    *,
    examples_per_label: int = 5,
    seed: int | None = 1,
    accuracy: float = 0.8,
) -> MethodResult:
    """Return a plausible MethodResult for report and aggregation tests."""
    return MethodResult(
        method=method,
        examples_per_label=examples_per_label,
        seed=seed,
        correct=int(accuracy * 100),
        total=100,
        accuracy=accuracy,
        accuracy_ci_low=accuracy - 0.05,
        accuracy_ci_high=accuracy + 0.05,
        median_latency_ms=10.0,
        p95_latency_ms=20.0,
        input_tokens=0,
        list_price_cost_usd=Decimal(0),
    )


class KeywordEmbedder:
    """Embeds a text as a one-hot vector for the first known keyword it contains."""

    def __init__(self, keywords: Sequence[str]) -> None:
        """Remember the keyword order that defines the vector dimensions."""
        self._keywords = list(keywords)
        self.calls: list[list[str]] = []

    def embed(self, texts: Sequence[str]) -> FloatMatrix:
        """Return one one-hot row per text (a small constant keeps rows non-zero)."""
        self.calls.append(list(texts))
        rows = np.full((len(texts), len(self._keywords)), 0.01, dtype=np.float32)
        for row, text in enumerate(texts):
            for column, keyword in enumerate(self._keywords):
                if keyword in text:
                    rows[row, column] = 1.0
                    break
        return rows


class KeywordDecider:
    """Fake Jev: picks the catalog label whose keyword appears in the message."""

    def __init__(self, *, input_tokens: int | None = 100) -> None:
        """Configure the usage each fake call reports."""
        self._input_tokens = input_tokens
        self.calls: list[str] = []

    def decide(self, message: str, catalog: IntentCatalog) -> JevDecision:
        """Return the first label whose keyword is in the message."""
        self.calls.append(message)
        choice = next(
            (label for label in catalog.labels if label.split("_")[0] in message),
            catalog.labels[0],
        )
        return JevDecision(
            choice=choice,
            confidence=0.9,
            probabilities={label: float(label == choice) for label in catalog.labels},
            input_tokens=self._input_tokens,
            model="fake-jev",
            latency_ms=5.0,
        )


@pytest.fixture
def catalog() -> IntentCatalog:
    """Return the default two-label catalog."""
    return make_catalog()


@pytest.fixture(autouse=True)
def _restore_logging() -> Iterator[None]:
    """Undo configure_logging() so one test's handlers never leak into the next."""
    root = logging.getLogger()
    saved_handlers, saved_level = list(root.handlers), root.level
    yield
    root.handlers[:] = saved_handlers
    root.setLevel(saved_level)
