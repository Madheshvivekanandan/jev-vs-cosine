from pathlib import Path

import pytest
from pydantic import SecretStr, ValidationError

from app.core.settings import BenchmarkSettings
from app.domain.errors.configuration_error import ConfigurationError


def _settings(**overrides: object) -> BenchmarkSettings:
    # _env_file=None keeps the developer's real .env out of the tests.
    return BenchmarkSettings(_env_file=None, **overrides)  # type: ignore[call-arg]  # pydantic-settings init kwarg


@pytest.mark.parametrize(
    "url",
    [
        "https://api.typesafe.ai",
        "https://ai-gateway.vercel.sh/typesafe",
        "https://openrouter.ai/api",
        "https://opencode.ai/zen",
    ],
)
def test_jev_base_url_accepts_documented_routes(url: str) -> None:
    assert _settings(jev_base_url=url + "/").jev_base_url == url


@pytest.mark.parametrize(
    "url", ["http://api.typesafe.ai", "https://jev-agent.com", "https://api.typesafe.ai.evil.io"]
)
def test_jev_base_url_rejects_insecure_or_unknown_hosts(url: str) -> None:
    with pytest.raises(ValidationError, match="JEV_BASE_URL"):
        _settings(jev_base_url=url)


def test_require_jev_route_lists_every_missing_variable() -> None:
    with pytest.raises(ConfigurationError, match="JEV_API_KEY, JEV_BASE_URL, JEV_MODEL"):
        _settings().require_jev_route()


def test_require_jev_route_keeps_the_key_secret() -> None:
    route = _settings(
        jev_api_key=SecretStr("sk-very-secret"),
        jev_base_url="https://api.typesafe.ai",
        jev_model="jev-1.13.0",
    ).require_jev_route()

    assert route.model == "jev-1.13.0"
    assert "sk-very-secret" not in repr(route)


def test_settings_defaults_point_inside_the_project() -> None:
    settings = _settings()

    assert settings.results_dir == Path("results")
    assert settings.jev_max_total_input_tokens == 3_000_000


def test_route_id_combines_host_and_model() -> None:
    route = _settings(
        jev_api_key=SecretStr("public"),
        jev_base_url="https://opencode.ai/zen",
        jev_model="jev-1.13-free",
    ).require_jev_route()

    assert route.route_id == "opencode.ai/jev-1.13-free"
