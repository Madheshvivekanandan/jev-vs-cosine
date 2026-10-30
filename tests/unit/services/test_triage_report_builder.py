from app.domain.prediction import Prediction
from app.domain.triage_inputs import TriageInputs
from app.services.triage_report_builder import build_triage_report


def _run(answers: list[tuple[str, float]]) -> tuple[Prediction, ...]:
    # Message i's true label is "a"; each answer is (predicted label, confidence).
    return tuple(
        Prediction(f"m{i}", "a", label, 1.0, confidence=confidence)
        for i, (label, confidence) in enumerate(answers)
    )


def _inputs() -> TriageInputs:
    jev = _run([("a", 1.0), ("a", 0.95), ("b", 0.4), ("a", 0.99)])
    trained = _run([("a", 0.9), ("b", 0.3), ("a", 0.6), ("b", 0.95)])
    voting = _run([("a", 0.0), ("a", 0.0), ("a", 0.0), ("b", 0.0)])
    return TriageInputs(jev=jev, trained={5: (trained,)}, voting={5: (voting,)})


def test_build_triage_report_has_every_section() -> None:
    report = build_triage_report(_inputs(), sample_label="Probe x")

    for heading in (
        "# When to trust an answer",
        "## Jev: route only its confident answers",
        "## Classifier (method E)",
        "## Cheap first, Jev only when needed",
        "## How to read this",
    ):
        assert heading in report
    assert "Probe x: 4 messages" in report
    assert "Jev got 1 of 4 messages wrong in total." in report


def test_build_triage_report_rows_match_the_replayed_outcomes() -> None:
    report = build_triage_report(_inputs(), sample_label="Sample")

    # Jev at >= 0.95: 3 of 4 routed, all right; 1 left for a person.
    assert "| 0.95 | 75.0% | 100.0% | 0 | 1 |" in report
    # Nothing reaches 1.0 for the classifier, so its accuracy cell is a dash.
    assert "| 1.00 | 0.0% | – | 0 | 4 |" in report
    assert "| Jev alone | 0 | 75.0% | 100.0% |" in report
    assert "| Classifier alone | 5 | 50.0% | 0.0% |" in report
    # m0, m2 and m3 agree (m0 and m2 right, m3 wrong); only m1 goes to Jev, which is right.
    assert "| Cosine voting and classifier agree, else Jev | 5 | 75.0% | 25.0% |" in report
    # At >= 0.7 the classifier keeps m0 (right) and m3 (wrong); Jev answers m1 right, m2 wrong.
    assert "| Classifier confidence at least 0.7, else Jev | 5 | 50.0% | 50.0% |" in report
