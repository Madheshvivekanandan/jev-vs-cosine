"""Build TRIAGE.md: when to trust an answer, and cheap-first cascades that ask Jev less."""

from collections.abc import Mapping, Sequence
from typing import Final

from app.domain.cascade_outcome import CascadeOutcome
from app.domain.prediction import Prediction
from app.domain.triage import agreement_cascade, confidence_cascade, outcome_at_threshold, pool
from app.domain.triage_inputs import RunsPerSeed, TriageInputs

# A fixed grid, not tuned on any test set: readers pick their own trade-off from it.
THRESHOLDS: Final = (1.0, 0.99, 0.95, 0.9, 0.8, 0.5)
CASCADE_THRESHOLDS: Final = (0.9, 0.7, 0.5)

_THRESHOLD_HEADER: Final = (
    "| Route automatically when confidence is at least | Messages routed automatically | "
    "Accuracy of those | Wrong answers routed automatically | Sent to a person |\n"
    "|---|---|---|---|---|"
)
_CASCADE_HEADER: Final = (
    "| Strategy | Past examples per category | Accuracy | Messages sent to Jev |\n|---|---|---|---|"
)


def build_triage_report(inputs: TriageInputs, *, sample_label: str) -> str:
    """Return the full TRIAGE.md text for one test sample."""
    jev = inputs.jev
    wrong = sum(not p.is_correct for p in jev)
    sections = [
        "# When to trust an answer, and when to ask Jev",
        f"{sample_label}: {len(jev):,} messages. Everything here replays saved predictions, "
        "so it calls no model and costs nothing.",
        "## Jev: route only its confident answers",
        "\n".join([_THRESHOLD_HEADER, *(_threshold_row(jev, t) for t in THRESHOLDS)]),
        f"Jev got {wrong} of {len(jev):,} messages wrong in total.",
        "## Classifier (method E): the same, with its own probabilities",
        *_classifier_sections(inputs.trained),
        "## Cheap first, Jev only when needed",
        "\n".join([_CASCADE_HEADER, *_cascade_rows(inputs)]),
        _NOTES,
    ]
    return "\n\n".join(sections) + "\n"


def _threshold_row(predictions: Sequence[Prediction], threshold: float) -> str:
    outcome = outcome_at_threshold(predictions, threshold)
    accuracy = f"{outcome.routed_accuracy:.1%}" if outcome.routed else "–"
    return (
        f"| {threshold:.2f} | {outcome.routed_share:.1%} | {accuracy} | "
        f"{outcome.routed_wrong:,} | {outcome.total - outcome.routed:,} |"
    )


def _classifier_sections(trained: Mapping[int, RunsPerSeed]) -> list[str]:
    sections: list[str] = []
    for per_label, runs in sorted(trained.items()):
        pooled = [p for run in runs for p in run]
        rows = (_threshold_row(pooled, t) for t in THRESHOLDS)
        sections.append(
            f"With {per_label} past examples per category, pooled over {len(runs)} random draws "
            f"({len(pooled):,} answers):\n\n" + "\n".join([_THRESHOLD_HEADER, *rows])
        )
    return sections


def _cascade_rows(inputs: TriageInputs) -> list[str]:
    jev = inputs.jev
    rows = [_cascade_row("Jev alone", 0, pool([_jev_alone(jev)]))]
    for per_label, trained_runs in sorted(inputs.trained.items()):
        voting_runs = inputs.voting[per_label]
        alone = pool([_cheap_alone(run) for run in trained_runs])
        agree = pool(
            [agreement_cascade(v, t, jev) for v, t in zip(voting_runs, trained_runs, strict=True)]
        )
        rows.append(_cascade_row("Classifier alone", per_label, alone))
        rows.append(_cascade_row("Cosine voting and classifier agree, else Jev", per_label, agree))
        for threshold in CASCADE_THRESHOLDS:
            outcome = pool([confidence_cascade(run, jev, threshold) for run in trained_runs])
            name = f"Classifier confidence at least {threshold:.1f}, else Jev"
            rows.append(_cascade_row(name, per_label, outcome))
    return rows


def _cascade_row(name: str, per_label: int, outcome: CascadeOutcome) -> str:
    return f"| {name} | {per_label} | {outcome.accuracy:.1%} | {outcome.escalated_share:.1%} |"


def _jev_alone(jev: Sequence[Prediction]) -> CascadeOutcome:
    return CascadeOutcome(
        total=len(jev), correct=sum(p.is_correct for p in jev), escalated=len(jev)
    )


def _cheap_alone(run: Sequence[Prediction]) -> CascadeOutcome:
    return CascadeOutcome(total=len(run), correct=sum(p.is_correct for p in run), escalated=0)


_NOTES: Final = """## How to read this

- The thresholds are a fixed grid, not tuned on this sample, so no row is a best case picked
  after the fact. Choose the row that matches how many wrong answers you can let through.
- "Sent to a person" and "Messages sent to Jev" are what a live system would escalate.
  Jev's cost and latency apply only to the messages sent to it.
- Rows with past examples are pooled over the same random draws as REPORT.md, so their
  accuracy is the mean over draws. A cascade pairs each draw of the classifier with the same
  draw of cosine voting.
- Jev's confidence is its probability for the chosen option. The classifier's is scikit-learn's
  predicted probability for its top label. The two are not on the same scale, so compare
  each method's rows with each other, not across methods."""
