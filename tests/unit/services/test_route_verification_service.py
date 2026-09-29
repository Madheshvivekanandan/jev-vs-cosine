from collections.abc import Mapping

import pytest

from app.domain.reference_case import ReferenceCase
from app.services.route_verification_service import RouteVerificationService


def _case(case_id: str, tokens: int = 100) -> ReferenceCase:
    return ReferenceCase(
        case_id=case_id,
        source_url="u",
        reference_model="jev-1.13.0",
        state="hi",
        questions={"q": {"type": "noul", "instructions": "greeting?"}},
        reference_response={
            "answers": {"q": {"type": "noul", "noul": 0.9}},
            "usage": {"input_tokens": tokens},
        },
    )


class _EchoCaller:
    """Returns a fixed body for every request and records the calls."""

    def __init__(self, body: dict[str, object]) -> None:
        self.body = body
        self.calls: list[tuple[object, Mapping[str, object]]] = []

    def call(self, state: object, questions: Mapping[str, object]) -> dict[str, object]:
        self.calls.append((state, questions))
        return self.body


def test_verify_matches_when_the_route_answers_like_the_reference() -> None:
    caller = _EchoCaller(
        {"answers": {"q": {"type": "noul", "noul": 0.91}}, "usage": {"input_tokens": 100}}
    )

    checks = RouteVerificationService(caller).verify([_case("a")], max_cases=6)

    assert [c.comparison.matches for c in checks] == [True]
    assert caller.calls == [("hi", {"q": {"type": "noul", "instructions": "greeting?"}})]


def test_verify_flags_a_changed_route() -> None:
    caller = _EchoCaller(
        {"answers": {"q": {"type": "noul", "noul": 0.2}}, "usage": {"input_tokens": 90}}
    )

    checks = RouteVerificationService(caller).verify([_case("a")], max_cases=1)

    assert not checks[0].comparison.matches


def test_verify_replays_at_most_max_cases_in_order() -> None:
    caller = _EchoCaller({"answers": {}, "usage": {}})

    checks = RouteVerificationService(caller).verify(
        [_case("a"), _case("b"), _case("c")], max_cases=2
    )

    assert [c.comparison.case_id for c in checks] == ["a", "b"]


def test_verify_rejects_a_non_positive_case_count() -> None:
    with pytest.raises(ValueError, match="at least 1"):
        RouteVerificationService(_EchoCaller({})).verify([_case("a")], max_cases=0)
