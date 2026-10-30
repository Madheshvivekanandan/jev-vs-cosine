"""Confidence thresholds and cheap-first cascades, computed from saved predictions.

Every function here replays predictions that were already made, so it calls no model and
costs nothing. Prediction lists passed together must cover the same messages in the same
order, as every method's run does for one test sample.
"""

from collections.abc import Sequence

from app.domain.cascade_outcome import CascadeOutcome
from app.domain.errors.dataset_error import DatasetError
from app.domain.prediction import Prediction
from app.domain.threshold_outcome import ThresholdOutcome


def outcome_at_threshold(predictions: Sequence[Prediction], threshold: float) -> ThresholdOutcome:
    """Return what routing only the answers with confidence >= `threshold` would give.

    Raises:
        DatasetError: If a prediction carries no confidence.
    """
    routed = [p for p in predictions if _confidence(p) >= threshold]
    return ThresholdOutcome(
        threshold=threshold,
        total=len(predictions),
        routed=len(routed),
        routed_correct=sum(p.is_correct for p in routed),
    )


def agreement_cascade(
    first: Sequence[Prediction], second: Sequence[Prediction], fallback: Sequence[Prediction]
) -> CascadeOutcome:
    """Keep the answer when two cheap methods agree; otherwise use the fallback's answer.

    Raises:
        DatasetError: If the three lists do not cover the same messages in the same order.
    """
    _ensure_aligned(first, second, fallback)
    correct = escalated = 0
    for a, b, jev in zip(first, second, fallback, strict=True):
        if a.predicted_label == b.predicted_label:
            correct += a.is_correct
        else:
            escalated += 1
            correct += jev.is_correct
    return CascadeOutcome(total=len(first), correct=correct, escalated=escalated)


def confidence_cascade(
    cheap: Sequence[Prediction], fallback: Sequence[Prediction], threshold: float
) -> CascadeOutcome:
    """Keep the cheap answer at confidence >= `threshold`; otherwise use the fallback's.

    Raises:
        DatasetError: If the lists do not cover the same messages in the same order, or a
            cheap prediction carries no confidence.
    """
    _ensure_aligned(cheap, fallback)
    correct = escalated = 0
    for guess, jev in zip(cheap, fallback, strict=True):
        if _confidence(guess) >= threshold:
            correct += guess.is_correct
        else:
            escalated += 1
            correct += jev.is_correct
    return CascadeOutcome(total=len(cheap), correct=correct, escalated=escalated)


def pool(outcomes: Sequence[CascadeOutcome]) -> CascadeOutcome:
    """Return the outcomes summed, e.g. over random draws (accuracy becomes their mean)."""
    return CascadeOutcome(
        total=sum(o.total for o in outcomes),
        correct=sum(o.correct for o in outcomes),
        escalated=sum(o.escalated for o in outcomes),
    )


def _confidence(prediction: Prediction) -> float:
    if prediction.confidence is None:
        raise DatasetError("a prediction has no confidence; re-run its method to record it")
    return prediction.confidence


def _ensure_aligned(*runs: Sequence[Prediction]) -> None:
    keys = [[(p.text, p.true_label) for p in run] for run in runs]
    if any(other != keys[0] for other in keys[1:]):
        raise DatasetError("prediction lists cover different messages; compare one sample only")
