"""Adapter from the official TypeSafe SDK to the JevDecider port."""

import time
from collections.abc import Callable, Mapping
from typing import Final, Protocol

from pydantic import SecretStr
from typesafe_sdk import (
    Choice,
    JSONContent,
    Question,
    RetryPolicy,
    SystemOneResponse,
    TypeSafeAPIConnectionError,
    TypeSafeAPITimeoutError,
    TypeSafeAuthenticationError,
    TypeSafeClient,
    TypeSafeError,
    TypeSafeInternalServerError,
    TypeSafePermissionDeniedError,
    TypeSafeRateLimitError,
)

from app.domain.errors.configuration_error import ConfigurationError
from app.domain.errors.jev_request_error import JevRequestError
from app.domain.errors.jev_unavailable_error import JevUnavailableError
from app.domain.intent_catalog import IntentCatalog
from app.domain.jev_decision import JevDecision

_QUESTION_NAME: Final = "intent"
_STATE_FIELD: Final = "customer_message"
_TRANSIENT_ERRORS: Final = (
    TypeSafeRateLimitError,
    TypeSafeAPIConnectionError,
    TypeSafeAPITimeoutError,
    TypeSafeInternalServerError,
)
_CREDENTIAL_ERRORS: Final = (TypeSafeAuthenticationError, TypeSafePermissionDeniedError)


class SystemOneClient(Protocol):
    """The one TypeSafeClient method this adapter needs (lets tests pass a fake)."""

    def system_one(
        self, state: JSONContent, questions: Mapping[str, Question], *, model: str | None = None
    ) -> SystemOneResponse:
        """Answer named questions about the state."""
        ...


def create_typesafe_client(
    *, api_key: SecretStr, base_url: str, timeout_seconds: float, max_retries: int
) -> TypeSafeClient:
    """Return an SDK client for the configured route.

    Retries use the SDK's jittered exponential backoff on 408/429/5xx, honouring
    Retry-After, within its 30 s total budget. `max_retries` is configurable because
    some free routes count every retry against a daily request cap. With retries on,
    a call's measured latency includes any retry waits.

    Raises:
        ConfigurationError: If the SDK rejects the key or settings (e.g. a malformed key).
    """
    try:
        return TypeSafeClient(
            api_key=api_key.get_secret_value(),
            base_url=base_url,
            timeout=timeout_seconds,
            retry=RetryPolicy(max_retries=max_retries),
        )
    except TypeSafeError as exc:
        raise ConfigurationError(f"Jev client configuration rejected: {exc}") from exc


class TypeSafeJevDecider:
    """Asks Jev one Choice question per message: which catalog intent it expresses."""

    def __init__(
        self,
        client: SystemOneClient,
        *,
        model: str,
        clock: Callable[[], float] = time.perf_counter,
    ) -> None:
        """Wire the adapter to an SDK client and the pinned model id."""
        self._client = client
        self._model = model
        self._clock = clock

    def decide(self, message: str, catalog: IntentCatalog) -> JevDecision:
        """Return Jev's intent for `message`, validated against the catalog.

        Raises:
            JevUnavailableError: Rate limit, timeout, network or 5xx after SDK retries.
            ConfigurationError: The API key was rejected.
            JevRequestError: The request was rejected or the answer was unusable.
        """
        question = Choice(instructions=catalog.instructions, criteria=dict(catalog.descriptions))
        started = self._clock()
        response = self._call({_STATE_FIELD: message}, {_QUESTION_NAME: question})
        latency_ms = (self._clock() - started) * 1000
        answer = response.choices.get(_QUESTION_NAME)
        # Schema-valid is not the same as valid: re-check the choice in our own code.
        if answer is None or answer.choice not in catalog.descriptions:
            raise JevRequestError("Jev returned no usable choice for the intent question")
        return JevDecision(
            choice=answer.choice,
            confidence=answer.confidence,
            probabilities=dict(answer.probabilities),
            input_tokens=response.usage.input_tokens,
            model=response.model,
            latency_ms=latency_ms,
        )

    def _call(self, state: JSONContent, questions: Mapping[str, Question]) -> SystemOneResponse:
        try:
            return self._client.system_one(state, questions, model=self._model)
        except _TRANSIENT_ERRORS as exc:
            raise JevUnavailableError(f"Jev unavailable after retries: {exc}") from exc
        except _CREDENTIAL_ERRORS as exc:
            # str() of an SDK API error is the provider's own message (e.g. "add a credit
            # card") plus the request id; it never contains the Authorization header.
            raise ConfigurationError(f"Jev refused the key or account: {exc}") from exc
        except TypeSafeError as exc:
            raise JevRequestError(f"Jev rejected the request: {exc}") from exc
