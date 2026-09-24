"""Method B: ask Jev for every test message, safely and resumably."""

import hashlib
import json
import logging
import math
from collections.abc import Sequence
from decimal import Decimal
from typing import Final

from app.domain.intent_catalog import IntentCatalog
from app.domain.jev_decision import JevDecision
from app.domain.jev_run_estimate import JevRunEstimate
from app.domain.labeled_message import LabeledMessage
from app.domain.prediction import Prediction
from app.repositories.jev_decision_cache_repository import JevDecisionCacheRepository
from app.services.call_pacer import CallPacer
from app.services.ports.jev_decider import JevDecider
from app.services.token_budget import TokenBudget

logger = logging.getLogger(__name__)

# Pre-flight token estimate. TypeSafe publishes no tokenizer or count-tokens endpoint,
# so this is a deliberately conservative heuristic: ~4 characters per token plus the
# ~275-330 token fixed overhead seen on tiny requests in TypeSafe's and OpenRouter's
# documented examples. Once real usage is cached, the observed average takes over.
_CHARS_PER_TOKEN: Final = 4
_REQUEST_OVERHEAD_TOKENS: Final = 350
_OBSERVED_MARGIN_PERCENT: Final = 10
_TOKENS_PER_MILLION: Final = Decimal(1_000_000)


class JevBenchmarkService:
    """Runs Jev over the test set with a cache, a hard token budget and call pacing.

    Every answer is cached before the next call, so a run stopped by a rate limit or
    the budget resumes where it left off and never pays twice for a message.
    """

    def __init__(
        self,
        decider: JevDecider,
        cache: JevDecisionCacheRepository,
        budget: TokenBudget,
        pacer: CallPacer,
    ) -> None:
        """Wire the service to its collaborators."""
        self._decider = decider
        self._cache = cache
        self._budget = budget
        self._pacer = pacer

    def estimate(
        self,
        catalog: IntentCatalog,
        test_set: Sequence[LabeledMessage],
        *,
        route_id: str,
        price_usd_per_million_tokens: Decimal,
    ) -> JevRunEstimate:
        """Return what a run would cost without calling Jev (the dry run)."""
        uncached = [
            m for m in test_set if self._cache.get(cache_key(route_id, catalog, m.text)) is None
        ]
        estimated_tokens = sum(self._estimate_tokens(catalog, m.text) for m in uncached)
        return JevRunEstimate(
            cached_messages=len(test_set) - len(uncached),
            uncached_messages=len(uncached),
            estimated_tokens=estimated_tokens,
            estimated_list_price_usd=Decimal(estimated_tokens)
            * price_usd_per_million_tokens
            / _TOKENS_PER_MILLION,
            remaining_budget_tokens=self._budget.remaining_tokens,
        )

    def run(
        self, catalog: IntentCatalog, test_set: Sequence[LabeledMessage], *, route_id: str
    ) -> list[Prediction]:
        """Return Jev's prediction for every message, calling Jev only for uncached ones.

        `route_id` (host/model) namespaces the cache so answers from different routes
        or models are never mixed.

        Raises:
            BudgetExceededError: The next call would exceed the token ceiling.
            JevUnavailableError: Jev stayed unavailable after the SDK's retries.
            JevRequestError: Jev rejected a request or returned an unusable answer.
            ConfigurationError: The route rejected the API key or account.
        """
        predictions: list[Prediction] = []
        fresh_calls = 0
        for message in test_set:
            key = cache_key(route_id, catalog, message.text)
            decision = self._cache.get(key)
            if decision is None:
                decision = self._decide_fresh(catalog, message.text, key)
                fresh_calls += 1
            predictions.append(_to_prediction(message, decision, self._cache.charged_tokens(key)))
        logger.info(
            "jev_run_complete",
            extra={"fresh_calls": fresh_calls, "spent_tokens": self._budget.spent_tokens},
        )
        return predictions

    def served_models(
        self, catalog: IntentCatalog, test_set: Sequence[LabeledMessage], *, route_id: str
    ) -> list[str]:
        """Return the distinct model ids the route reported for the cached answers."""
        decisions = (self._cache.get(cache_key(route_id, catalog, m.text)) for m in test_set)
        return sorted({decision.model for decision in decisions if decision is not None})

    def _decide_fresh(self, catalog: IntentCatalog, text: str, key: str) -> JevDecision:
        estimated_tokens = self._estimate_tokens(catalog, text)
        self._budget.ensure_affordable(estimated_tokens)
        self._pacer.wait_turn()
        decision = self._decider.decide(text, catalog)
        used_tokens = (
            decision.input_tokens if decision.input_tokens is not None else estimated_tokens
        )
        self._budget.record(used_tokens)
        self._cache.put(key, decision, charged_tokens=used_tokens)
        if decision.input_tokens is None:
            logger.warning("jev_usage_not_reported", extra={"charged_estimate": used_tokens})
        logger.debug(
            "jev_call",
            extra={
                "input_tokens": decision.input_tokens,
                "latency_ms": round(decision.latency_ms, 1),
                "model": decision.model,
            },
        )
        return decision

    def _estimate_tokens(self, catalog: IntentCatalog, text: str) -> int:
        observed = self._cache.average_input_tokens()
        if observed is not None:
            # Integer percent arithmetic: `observed * 1.1` gives 220.00000000000003 for 200.
            return math.ceil(observed * (100 + _OBSERVED_MARGIN_PERCENT) / 100)
        characters = (
            len(catalog.instructions)
            + len(text)
            + sum(
                len(label) + len(description) for label, description in catalog.descriptions.items()
            )
        )
        return _REQUEST_OVERHEAD_TOKENS + math.ceil(characters / _CHARS_PER_TOKEN)


def cache_key(route_id: str, catalog: IntentCatalog, text: str) -> str:
    """Return the cache key for one (route and model, catalog wording, message) combination."""
    canonical = json.dumps(
        {"route": route_id, "catalog": catalog.fingerprint(), "message": text}, sort_keys=True
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _to_prediction(
    message: LabeledMessage, decision: JevDecision, charged_tokens: int
) -> Prediction:
    return Prediction(
        text=message.text,
        true_label=message.label,
        predicted_label=decision.choice,
        latency_ms=decision.latency_ms,
        input_tokens=charged_tokens,
    )
