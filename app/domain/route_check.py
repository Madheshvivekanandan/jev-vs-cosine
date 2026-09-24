"""The outcome of replaying one reference case through the configured Jev route."""

from collections.abc import Mapping
from dataclasses import dataclass

from app.domain.reference_comparison import ReferenceComparison


@dataclass(frozen=True, slots=True)
class RouteCheck:
    """A comparison plus the raw response body, kept as evidence."""

    comparison: ReferenceComparison
    observed_response: Mapping[str, object]
