"""Load the published Jev reference cases used to verify a route."""

from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError

from app.domain.errors.configuration_error import ConfigurationError
from app.domain.reference_case import ReferenceCase


class _Request(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    # Any: state is arbitrary JSON by the TypeSafe spec; it is sent through untouched.
    state: Any
    questions: dict[str, dict[str, Any]] = Field(min_length=1)


class _CaseRecord(BaseModel):
    """One entry of fingerprints/*.json."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1)
    source_url: str = Field(min_length=1)
    reference_model: str = Field(min_length=1)
    request: _Request
    # Any: a TypeSafe response body, compared field by field in the domain.
    reference_response: dict[str, Any]


_CASES = TypeAdapter(list[_CaseRecord])


def load_reference_cases(path: Path) -> list[ReferenceCase]:
    """Return the reference cases stored at `path`, in file order.

    Raises:
        ConfigurationError: If the file is missing, invalid, or empty.
    """
    if not path.exists():
        raise ConfigurationError(f"reference cases {path} not found")
    try:
        records = _CASES.validate_json(path.read_text(encoding="utf-8"))
    except ValidationError as exc:
        raise ConfigurationError(f"reference cases {path} are invalid") from exc
    if not records:
        raise ConfigurationError(f"reference cases {path} are empty")
    return [
        ReferenceCase(
            case_id=record.id,
            source_url=record.source_url,
            reference_model=record.reference_model,
            state=record.request.state,
            questions=record.request.questions,
            reference_response=record.reference_response,
        )
        for record in records
    ]
