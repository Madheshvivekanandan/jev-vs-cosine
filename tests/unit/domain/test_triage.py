import pytest

from app.domain.cascade_outcome import CascadeOutcome
from app.domain.errors.dataset_error import DatasetError
from app.domain.prediction import Prediction
from app.domain.threshold_outcome import ThresholdOutcome
from app.domain.triage import agreement_cascade, confidence_cascade, outcome_at_threshold, pool


def _guess(text: str, predicted: str, confidence: float | None = None) -> Prediction:
    # Every message's true label is "a", so a guess of "a" is correct.
    return Prediction(text, "a", predicted, 1.0, confidence=confidence)


def test_outcome_at_threshold_includes_answers_exactly_at_the_threshold() -> None:
    predictions = [_guess("m1", "a", 1.0), _guess("m2", "b", 0.95), _guess("m3", "a", 0.5)]

    outcome = outcome_at_threshold(predictions, 0.95)

    assert outcome == ThresholdOutcome(threshold=0.95, total=3, routed=2, routed_correct=1)
    assert (outcome.routed_wrong, outcome.routed_share, outcome.routed_accuracy) == (1, 2 / 3, 0.5)


def test_outcome_at_threshold_without_confidence_raises() -> None:
    with pytest.raises(DatasetError, match="no confidence"):
        outcome_at_threshold([_guess("m1", "a")], 0.5)


def test_threshold_outcome_with_nothing_routed_reports_zero() -> None:
    outcome = ThresholdOutcome(threshold=1.0, total=0, routed=0, routed_correct=0)

    assert (outcome.routed_share, outcome.routed_accuracy) == (0.0, 0.0)


def test_agreement_cascade_keeps_agreed_answers_and_escalates_the_rest() -> None:
    voting = [_guess("m1", "a"), _guess("m2", "b"), _guess("m3", "b")]
    trained = [_guess("m1", "a"), _guess("m2", "a"), _guess("m3", "b")]
    jev = [_guess("m1", "b"), _guess("m2", "a"), _guess("m3", "a")]

    outcome = agreement_cascade(voting, trained, jev)

    # m1 agreed and right, m2 escalated and Jev right, m3 agreed and wrong (Jev not asked).
    assert outcome == CascadeOutcome(total=3, correct=2, escalated=1)


def test_agreement_cascade_on_different_messages_raises() -> None:
    with pytest.raises(DatasetError, match="different messages"):
        agreement_cascade([_guess("m1", "a")], [_guess("m2", "a")], [_guess("m1", "a")])


def test_confidence_cascade_escalates_below_the_threshold_only() -> None:
    cheap = [_guess("m1", "b", 0.9), _guess("m2", "b", 0.89), _guess("m3", "a", 0.2)]
    jev = [_guess("m1", "a"), _guess("m2", "a"), _guess("m3", "b")]

    outcome = confidence_cascade(cheap, jev, 0.9)

    assert outcome == CascadeOutcome(total=3, correct=1, escalated=2)
    assert outcome.escalated_share == 2 / 3


def test_pool_sums_draws_so_accuracy_is_their_mean() -> None:
    pooled = pool(
        [
            CascadeOutcome(total=10, correct=8, escalated=1),
            CascadeOutcome(total=10, correct=6, escalated=3),
        ]
    )

    assert (pooled.accuracy, pooled.escalated_share) == (0.7, 0.2)


def test_cascade_outcome_of_nothing_is_zero() -> None:
    empty = pool([])

    assert (empty.accuracy, empty.escalated_share) == (0.0, 0.0)
