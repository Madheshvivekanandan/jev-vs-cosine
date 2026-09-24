"""Adapter that sends a published request verbatim and returns the whole response body."""

from collections.abc import Mapping
from typing import cast

from typesafe_sdk import JSONContent, Question

from app.clients.typesafe_jev_decider import SystemOneClient, call_system_one


class TypeSafeRawCaller:
    """Replays raw TypeSafe wire JSON through the configured route (for verify-route)."""

    def __init__(self, client: SystemOneClient, *, model: str) -> None:
        """Wire the adapter to an SDK client and the route's model id."""
        self._client = client
        self._model = model

    def call(self, state: object, questions: Mapping[str, object]) -> dict[str, object]:
        """Return the response body, so every answer field can be compared.

        Raises:
            JevUnavailableError: Rate limit, timeout, network or 5xx after SDK retries.
            ConfigurationError: The route rejected the key or account.
            JevRequestError: Any other rejection.
        """
        # The cases are published TypeSafe wire JSON; the SDK accepts raw question dicts
        # (QuestionModel), so this single cast is the typed boundary for replayed input.
        response = call_system_one(
            self._client,
            cast("JSONContent", state),
            cast("Mapping[str, Question]", questions),
            model=self._model,
        )
        return cast("dict[str, object]", response.model_dump(mode="json"))
