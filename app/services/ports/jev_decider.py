"""Port for asking Jev which intent a message expresses."""

from typing import Protocol

from app.domain.intent_catalog import IntentCatalog
from app.domain.jev_decision import JevDecision


class JevDecider(Protocol):
    """Anything that answers one intent question for one message."""

    def decide(self, message: str, catalog: IntentCatalog) -> JevDecision:
        """Return Jev's choice among `catalog.labels` for `message`.

        Raises:
            JevUnavailableError: Transient failure that outlasted retries.
            JevRequestError: The request was rejected or the answer was unusable.
            ConfigurationError: The route rejected the API key or account.
        """
        ...
