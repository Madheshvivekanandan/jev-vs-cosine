"""Port for sending one raw TypeSafe-format request and getting the raw response back."""

from collections.abc import Mapping
from typing import Protocol


class SystemOneCaller(Protocol):
    """Anything that answers a raw System One request with a TypeSafe-format body."""

    def call(self, state: object, questions: Mapping[str, object]) -> dict[str, object]:
        """Return the response body as JSON-compatible data.

        Raises:
            JevUnavailableError: Transient failure that outlasted retries.
            ConfigurationError: The route rejected the key or account.
            JevRequestError: The request was rejected.
        """
        ...
