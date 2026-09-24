import pytest

from app.clients.cross_encoder_scorer import CrossEncoderScorer


def test_score_returns_one_float_per_pair() -> None:
    scorer = CrossEncoderScorer(lambda pairs: [[0.25] for _ in pairs])

    assert scorer.score([("q", "a"), ("q", "b")]) == [0.25, 0.25]


def test_score_when_model_returns_wrong_count_raises() -> None:
    scorer = CrossEncoderScorer(lambda _pairs: [0.1])

    with pytest.raises(ValueError, match="unexpected number"):
        scorer.score([("q", "a"), ("q", "b")])
