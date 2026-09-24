"""Load the versioned intent catalog (the "prompt" both methods share)."""

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.domain.errors.configuration_error import ConfigurationError
from app.domain.intent_catalog import IntentCatalog


class _CatalogFile(BaseModel):
    """Shape of prompts/*.json; unknown keys are rejected so typos fail loudly."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    version: str = Field(min_length=1)
    instructions: str = Field(min_length=1)
    descriptions: dict[str, str] = Field(min_length=1)


def load_intent_catalog(path: Path) -> IntentCatalog:
    """Return the catalog stored at `path`.

    Raises:
        ConfigurationError: If the file is missing or does not match the expected shape.
    """
    if not path.exists():
        raise ConfigurationError(f"intent catalog {path} not found")
    try:
        parsed = _CatalogFile.model_validate_json(path.read_text(encoding="utf-8"))
    except ValidationError as exc:
        raise ConfigurationError(f"intent catalog {path} is invalid") from exc
    if any(not description.strip() for description in parsed.descriptions.values()):
        raise ConfigurationError(f"intent catalog {path} has an empty description")
    return IntentCatalog(
        version=parsed.version,
        instructions=parsed.instructions,
        descriptions=parsed.descriptions,
    )
