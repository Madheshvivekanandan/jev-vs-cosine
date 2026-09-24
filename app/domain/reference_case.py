"""A published Jev request with the answer TypeSafe-served Jev gave it."""

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ReferenceCase:
    """One fingerprint: replaying `state` and `questions` should reproduce the reference.

    `state` and `questions` are raw TypeSafe wire JSON, sent exactly as published.
    """

    case_id: str
    source_url: str
    reference_model: str
    state: object
    questions: Mapping[str, object]
    reference_response: Mapping[str, object]
