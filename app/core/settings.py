"""Typed settings, read from the environment and the git-ignored .env file."""

from decimal import Decimal
from pathlib import Path
from typing import Final, Literal
from urllib.parse import urlparse

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.jev_route import JevRoute
from app.domain.errors.configuration_error import ConfigurationError

# Only routes documented to serve Jev with the TypeSafe wire format. An allow-list stops a
# typo or a lookalike reseller from receiving the API key. Cost as checked on 2026-09-24:
# opencode.ai (jev-1.13-free, $0, anonymous), ai-gateway.vercel.sh ($5/month free credit,
# card on file), api.typesafe.ai ($5 signup credit; signups paused), openrouter.ai (paid).
ALLOWED_JEV_HOSTS: Final = frozenset(
    {"opencode.ai", "ai-gateway.vercel.sh", "api.typesafe.ai", "openrouter.ai"}
)


class BenchmarkSettings(BaseSettings):
    """All configuration; see .env.example for every variable and its meaning."""

    # hide_input_in_errors: a misspelled key in .env must not echo its value in the error.
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="forbid", hide_input_in_errors=True
    )

    jev_api_key: SecretStr | None = None
    jev_base_url: str | None = None
    jev_model: str | None = None
    jev_timeout_seconds: float = Field(default=30.0, gt=0, le=120)
    # OpenCode Zen counts every request, retries included, against its daily free cap.
    jev_max_retries: int = Field(default=2, ge=0, le=5)
    jev_max_total_input_tokens: int = Field(default=3_000_000, gt=0)
    jev_min_seconds_between_calls: float = Field(default=0.0, ge=0, le=60)
    # TypeSafe list price (docs.typesafe.ai/models, checked 2026-09-23); output is free.
    jev_price_usd_per_million_input_tokens: Decimal = Field(default=Decimal("0.042"), ge=0)
    embedding_model_name: str = "BAAI/bge-small-en-v1.5"
    embedding_model_revision: str = "5c38ec7c405ec4b44b94cc5a9bb96e735b38267a"
    cross_encoder_model_name: str = "BAAI/bge-reranker-v2-m3"
    cross_encoder_model_revision: str = "953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e"
    data_dir: Path = Path("data")
    cache_dir: Path = Path(".cache")
    results_dir: Path = Path("results")
    catalog_path: Path = Path("prompts/banking77_intents.v1.json")
    probes_dir: Path = Path("probes")
    reference_cases_path: Path = Path("fingerprints/typesafe_reference.v2.json")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    @field_validator("jev_base_url")
    @classmethod
    def _check_jev_base_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        parsed = urlparse(value)
        if parsed.scheme != "https" or parsed.hostname not in ALLOWED_JEV_HOSTS:
            raise ValueError(f"JEV_BASE_URL must be https on one of {sorted(ALLOWED_JEV_HOSTS)}")
        return value.rstrip("/")

    def require_jev_route(self) -> JevRoute:
        """Return the Jev route, or explain exactly which variables are missing.

        Raises:
            ConfigurationError: If JEV_API_KEY, JEV_BASE_URL or JEV_MODEL is unset.
        """
        missing = [
            name
            for name, value in (
                ("JEV_API_KEY", self.jev_api_key),
                ("JEV_BASE_URL", self.jev_base_url),
                ("JEV_MODEL", self.jev_model),
            )
            if not value
        ]
        if missing or self.jev_api_key is None or not self.jev_base_url or not self.jev_model:
            raise ConfigurationError(f"set {', '.join(missing)} in .env (see .env.example)")
        return JevRoute(api_key=self.jev_api_key, base_url=self.jev_base_url, model=self.jev_model)
