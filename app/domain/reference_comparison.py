"""Compare a live Jev response with a published TypeSafe reference response."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final

# Jev is consistent, not deterministic: TypeSafe and independent audits measured a
# run-to-run standard deviation of about 0.01 on the same request. 0.05 is roughly 5 sigma.
PROBABILITY_TOLERANCE: Final = 0.05


@dataclass(frozen=True, slots=True)
class ReferenceComparison:
    """How closely one live response matches its reference."""

    case_id: str
    reference_input_tokens: int
    observed_input_tokens: int | None
    same_decisions: bool
    max_probability_gap: float

    @property
    def tokens_match(self) -> bool:
        """Return whether the input token counts are identical (same template and tokenizer)."""
        return self.observed_input_tokens == self.reference_input_tokens

    @property
    def matches(self) -> bool:
        """Return whether the response is consistent with the same model serving it."""
        return (
            self.tokens_match
            and self.same_decisions
            and self.max_probability_gap <= PROBABILITY_TOLERANCE
        )


def compare_to_reference(
    case_id: str, reference: Mapping[str, object], observed: Mapping[str, object]
) -> ReferenceComparison:
    """Compare two TypeSafe-format response bodies answer by answer."""
    reference_answers = _answers(reference)
    observed_answers = _answers(observed)
    same = reference_answers.keys() == observed_answers.keys()
    gap = 0.0
    for name, expected in reference_answers.items():
        actual = observed_answers.get(name, {})
        same = same and _decision(expected) == _decision(actual)
        gap = max(gap, _probability_gap(expected, actual))
    return ReferenceComparison(
        case_id=case_id,
        reference_input_tokens=_input_tokens(reference) or 0,
        observed_input_tokens=_input_tokens(observed),
        same_decisions=same,
        max_probability_gap=gap,
    )


def _answers(body: Mapping[str, object]) -> dict[str, Mapping[str, object]]:
    answers = body.get("answers")
    if not isinstance(answers, Mapping):
        return {}
    return {str(k): v for k, v in answers.items() if isinstance(v, Mapping)}


def _input_tokens(body: Mapping[str, object]) -> int | None:
    usage = body.get("usage")
    tokens = usage.get("input_tokens") if isinstance(usage, Mapping) else None
    return tokens if isinstance(tokens, int) else None


def _decision(answer: Mapping[str, object]) -> object:
    """The part of an answer that must agree exactly: the chosen option or the yes/no side."""
    if answer.get("type") == "choice":
        return answer.get("choice")
    if answer.get("type") == "score":
        return round(_number(answer.get("score")))
    return _number(answer.get("noul")) >= 0.5


def _probability_gap(expected: Mapping[str, object], actual: Mapping[str, object]) -> float:
    if expected.get("type") == "noul":
        return abs(_number(expected.get("noul")) - _number(actual.get("noul")))
    wanted = expected.get("probabilities")
    got = actual.get("probabilities")
    if not isinstance(wanted, Mapping) or not isinstance(got, Mapping):
        return 1.0
    keys = {str(k) for k in wanted} | {str(k) for k in got}
    wanted_by_key = {str(k): v for k, v in wanted.items()}
    got_by_key = {str(k): v for k, v in got.items()}
    return max(abs(_number(wanted_by_key.get(k)) - _number(got_by_key.get(k))) for k in keys)


def _number(value: object) -> float:
    return float(value) if isinstance(value, int | float) and not isinstance(value, bool) else 0.0
