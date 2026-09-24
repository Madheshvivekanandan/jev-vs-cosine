import numpy as np
import pytest

from app.clients.logistic_regression_trainer import LogisticRegressionTrainer
from app.services.vector_types import FloatMatrix


def _vectors(rows: list[list[float]]) -> FloatMatrix:
    return np.array(rows, dtype=np.float32)


def test_fit_then_predict_separable_labels() -> None:
    vectors = _vectors([[1, 0], [0.9, 0.1], [0, 1], [0.1, 0.9]])
    model = LogisticRegressionTrainer().fit(vectors, ["a", "a", "b", "b"])

    assert model.predict(_vectors([[0.95, 0.05], [0.05, 0.95]])) == ["a", "b"]


def test_fit_with_one_example_per_label_does_not_warn() -> None:
    # pytest turns warnings into errors here, so this fails if sklearn's
    # "unique classes" warning escapes the adapter.
    model = LogisticRegressionTrainer().fit(_vectors([[1, 0], [0, 1]]), ["a", "b"])

    assert model.predict(_vectors([[1, 0]])) == ["a"]


def test_fit_with_a_single_label_raises() -> None:
    with pytest.raises(ValueError, match="two distinct labels"):
        LogisticRegressionTrainer().fit(_vectors([[1, 0], [0.9, 0.1]]), ["a", "a"])
