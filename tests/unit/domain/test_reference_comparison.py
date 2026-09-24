import json
from pathlib import Path

import pytest

from app.domain.reference_comparison import compare_to_reference

_REFERENCE_CASES = (
    Path(__file__).resolve().parents[3] / "fingerprints" / "typesafe_reference.v1.json"
)


def _body(
    *, tokens: int = 422, billing: float = 1.0, urgent: float = 0.98, noul: float = 0.99
) -> dict[str, object]:
    return {
        "model": "m",
        "answers": {
            "department": {
                "type": "choice",
                "choice": "billing" if billing >= 0.5 else "technical",
                "probabilities": {"billing": billing, "technical": 1 - billing},
            },
            "urgency": {
                "type": "score",
                "score": 1.0,
                "probabilities": {"0": 0.0, "1": urgent, "2": 1 - urgent},
            },
            "refund": {"type": "noul", "noul": noul},
        },
        "usage": {"input_tokens": tokens, "output_tokens": 69},
    }


def test_opencode_recording_pair_counts_as_a_match() -> None:
    # The two live recordings in OpenCode's repo: TypeSafe direct vs Zen, 29 s apart.
    comparison = compare_to_reference("bridge", _body(urgent=0.98), _body(urgent=0.97))

    assert comparison.matches
    assert comparison.max_probability_gap == pytest.approx(0.01)


def test_a_different_token_count_is_not_a_match() -> None:
    comparison = compare_to_reference("c", _body(tokens=422), _body(tokens=500))

    assert not comparison.tokens_match
    assert not comparison.matches


def test_a_flipped_decision_is_not_a_match() -> None:
    comparison = compare_to_reference("c", _body(billing=1.0), _body(billing=0.2))

    assert not comparison.same_decisions
    assert not comparison.matches


def test_probabilities_far_apart_are_not_a_match() -> None:
    comparison = compare_to_reference("c", _body(noul=0.99), _body(noul=0.80))

    assert comparison.same_decisions
    assert not comparison.matches


def test_missing_answers_or_usage_never_match() -> None:
    comparison = compare_to_reference("c", _body(), {"answers": {}})

    assert comparison.observed_input_tokens is None
    assert not comparison.matches


def test_every_shipped_reference_case_matches_itself() -> None:
    for case in json.loads(_REFERENCE_CASES.read_text(encoding="utf-8")):
        reference = case["reference_response"]
        assert compare_to_reference(case["id"], reference, reference).matches, case["id"]
