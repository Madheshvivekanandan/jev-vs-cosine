from collections.abc import Mapping

import httpx2
import pytest
from pydantic import SecretStr
from typesafe_sdk import (
    Choice,
    ChoiceAnswer,
    JSONContent,
    Question,
    SystemOneResponse,
    TypeSafeAPITimeoutError,
    TypeSafeBadRequestError,
    TypeSafeClient,
    TypeSafePermissionDeniedError,
    TypeSafeRateLimitError,
    Usage,
)

from app.clients.typesafe_jev_decider import TypeSafeJevDecider, create_typesafe_client
from app.clients.typesafe_raw_caller import TypeSafeRawCaller
from app.domain.errors.configuration_error import ConfigurationError
from app.domain.errors.jev_request_error import JevRequestError
from app.domain.errors.jev_unavailable_error import JevUnavailableError
from app.domain.intent_catalog import IntentCatalog


class _FakeClient:
    """Stands in for TypeSafeClient.system_one; records what it was sent."""

    def __init__(
        self, response: SystemOneResponse | None = None, error: Exception | None = None
    ) -> None:
        self.response = response
        self.error = error
        self.requests: list[tuple[JSONContent, Mapping[str, Question], str | None]] = []

    def system_one(
        self, state: JSONContent, questions: Mapping[str, Question], *, model: str | None = None
    ) -> SystemOneResponse:
        self.requests.append((state, questions, model))
        if self.error is not None:
            raise self.error
        assert self.response is not None
        return self.response


def _response(choice: str = "alpha_intent", tokens: int | None = 1900) -> SystemOneResponse:
    return SystemOneResponse(
        model="jev-1.13.0",
        usage=Usage(input_tokens=tokens, output_tokens=40),
        answers={
            "intent": ChoiceAnswer(
                type="choice",
                choice=choice,
                confidence=0.7,
                probabilities={"alpha_intent": 0.85, "beta_intent": 0.15},
            )
        },
    )


def _api_error(error_type: type[TypeSafeBadRequestError], status: int, text: str) -> Exception:
    return error_type(status, {"error": {"message": text}}, httpx2.Headers())


def test_decide_sends_one_choice_question_built_from_the_catalog(catalog: IntentCatalog) -> None:
    client = _FakeClient(_response())
    decider = TypeSafeJevDecider(client, model="jev-1.13.0", clock=iter([1.0, 1.25]).__next__)

    decision = decider.decide("alpha please", catalog)

    state, questions, model = client.requests[0]
    question = questions["intent"]
    assert state == {"customer_message": "alpha please"}
    assert model == "jev-1.13.0"
    assert isinstance(question, Choice)
    assert dict(question.criteria) == dict(catalog.descriptions)
    assert (decision.choice, decision.input_tokens, decision.latency_ms) == (
        "alpha_intent",
        1900,
        250.0,
    )


def test_decide_rejects_a_choice_outside_the_catalog(catalog: IntentCatalog) -> None:
    decider = TypeSafeJevDecider(_FakeClient(_response(choice="gamma")), model="m")

    with pytest.raises(JevRequestError, match="no usable choice"):
        decider.decide("hi", catalog)


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (_api_error(TypeSafeRateLimitError, 429, "slow down"), JevUnavailableError),
        (TypeSafeAPITimeoutError(10.0), JevUnavailableError),
        (_api_error(TypeSafePermissionDeniedError, 403, "add a credit card"), ConfigurationError),
        (_api_error(TypeSafeBadRequestError, 400, "bad question"), JevRequestError),
    ],
)
def test_decide_translates_sdk_errors(
    catalog: IntentCatalog, error: Exception, expected: type[Exception]
) -> None:
    decider = TypeSafeJevDecider(_FakeClient(error=error), model="m")

    with pytest.raises(expected):
        decider.decide("hi", catalog)


def test_decide_surfaces_the_providers_reason(catalog: IntentCatalog) -> None:
    error = _api_error(TypeSafePermissionDeniedError, 403, "add a credit card")
    decider = TypeSafeJevDecider(_FakeClient(error=error), model="m")

    with pytest.raises(ConfigurationError, match="add a credit card"):
        decider.decide("hi", catalog)


def test_create_typesafe_client_uses_the_given_route() -> None:
    with create_typesafe_client(
        api_key=SecretStr("test-key-not-real"),
        base_url="https://api.typesafe.ai",
        timeout_seconds=5.0,
        max_retries=0,
    ) as client:
        assert isinstance(client, TypeSafeClient)


def test_create_typesafe_client_with_malformed_key_is_a_configuration_error() -> None:
    with pytest.raises(ConfigurationError, match="configuration rejected"):
        create_typesafe_client(
            api_key=SecretStr("has internal whitespace"),
            base_url="https://api.typesafe.ai",
            timeout_seconds=5.0,
            max_retries=0,
        )


def test_raw_caller_sends_the_request_verbatim_and_returns_the_body() -> None:
    client = _FakeClient(_response())
    caller = TypeSafeRawCaller(client, model="jev-1.13-free")

    body = caller.call(
        {"customer_message": "hi"}, {"intent": {"type": "choice", "criteria": {"a": None}}}
    )

    assert client.requests[0] == (
        {"customer_message": "hi"},
        {"intent": {"type": "choice", "criteria": {"a": None}}},
        "jev-1.13-free",
    )
    assert body["model"] == "jev-1.13.0"
    assert body["usage"] == {"input_tokens": 1900, "output_tokens": 40}


def test_raw_caller_translates_rate_limits() -> None:
    caller = TypeSafeRawCaller(
        _FakeClient(error=_api_error(TypeSafeRateLimitError, 429, "cap")), model="m"
    )

    with pytest.raises(JevUnavailableError):
        caller.call("hi", {"q": {"type": "noul"}})
