"""Every saved method result, bundled for the report and the chart."""

from collections.abc import Sequence
from dataclasses import dataclass

from app.domain.method_result import MethodResult


@dataclass(frozen=True, slots=True)
class BenchmarkResults:
    """All results for one test sample. Methods not run yet are None or empty.

    `cosine` holds method A plus every method C run, as `run-cosine` saves them, and
    `trained` holds every method E run, and `jev_with_examples` method B+.
    """

    cosine: Sequence[MethodResult]
    jev: MethodResult | None = None
    cross_encoder: MethodResult | None = None
    trained: Sequence[MethodResult] = ()
    jev_with_examples: MethodResult | None = None
