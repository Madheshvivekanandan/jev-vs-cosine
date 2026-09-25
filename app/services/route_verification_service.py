"""Check that the configured Jev route answers like TypeSafe-served Jev 1.13."""

import logging
from collections.abc import Sequence

from app.domain.reference_case import ReferenceCase
from app.domain.reference_comparison import compare_to_reference
from app.domain.route_check import RouteCheck
from app.services.ports.system_one_caller import SystemOneCaller

logger = logging.getLogger(__name__)


class RouteVerificationService:
    """Replays published reference cases and compares the answers.

    Matching token counts show the same prompt template and tokenizer; matching decisions
    and near-identical probabilities show the same model behaviour. Neither proves
    identity on its own, but a mismatch is strong evidence the route has changed.
    """

    def __init__(self, caller: SystemOneCaller) -> None:
        """Wire the service to a raw System One caller."""
        self._caller = caller

    def verify(self, cases: Sequence[ReferenceCase], *, max_cases: int) -> list[RouteCheck]:
        """Replay up to `max_cases` cases, in file order, and compare each with its reference.

        Raises:
            ValueError: If `max_cases` is not positive.
        """
        if max_cases < 1:
            raise ValueError("max_cases must be at least 1")
        checks: list[RouteCheck] = []
        for case in cases[:max_cases]:
            observed = self._caller.call(case.state, case.questions)
            comparison = compare_to_reference(
                case.case_id,
                case.reference_response,
                observed,
                strict_tokens=case.strict_tokens,
            )
            checks.append(RouteCheck(comparison, observed))
        matched = sum(1 for check in checks if check.comparison.matches)
        logger.info("route_verified", extra={"cases": len(checks), "matched": matched})
        return checks
