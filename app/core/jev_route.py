"""The fully-specified way to reach Jev: key, endpoint and pinned model."""

from dataclasses import dataclass
from urllib.parse import urlparse

from pydantic import SecretStr


@dataclass(frozen=True, slots=True)
class JevRoute:
    """Everything needed to call Jev; the key stays a SecretStr so repr never shows it."""

    api_key: SecretStr
    base_url: str
    model: str

    @property
    def route_id(self) -> str:
        """Return "host/model", which namespaces cached answers per route and model."""
        return f"{urlparse(self.base_url).hostname}/{self.model}"
