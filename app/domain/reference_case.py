"""A published Jev request with the answer TypeSafe-served Jev gave it."""

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ReferenceCase:
    """One fingerprint: replaying `state` and `questions` should reproduce the reference.

    `state` and `questions` are raw TypeSafe wire JSON, sent exactly as published.
    `strict_tokens` is True for dated live recordings, whose input-token count must match
    exactly, and False for undated documentation examples.
    """

    case_id: str
    source_url: str
    reference_model: str
    state: object
    questions: Mapping[str, object]
    reference_response: Mapping[str, object]
    strict_tokens: bool = True
