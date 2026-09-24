"""Adapter from scikit-learn's logistic regression to the ClassifierTrainer port."""

import warnings
from collections.abc import Sequence
from typing import Final

from sklearn.linear_model import LogisticRegression

from app.services.vector_types import FloatMatrix

# C was chosen on 1,500 held-out TRAINING messages outside the seed-1 example pool, never on
# the test split. Validation accuracy: C=1 (the default) 76.7% / 87.3%, C=10 81.1% / 89.5%,
# C=100 81.1% / 90.2% at 5 / 35 examples per category. The default underfits unit-length
# embeddings. lbfgs needs more than the default 100 iterations at this C.
_REGULARISATION_STRENGTH: Final = 100.0
_MAX_ITERATIONS: Final = 5000


class _FittedLogisticRegression:
    """A trained scikit-learn model behind the FittedClassifier port."""

    def __init__(self, model: LogisticRegression) -> None:
        self._model = model

    def predict(self, vectors: FloatMatrix) -> list[str]:
        """Return one predicted label per row."""
        return [str(label) for label in self._model.predict(vectors)]


class LogisticRegressionTrainer:
    """Trains multinomial logistic regression on embeddings (method E)."""

    def fit(self, vectors: FloatMatrix, labels: Sequence[str]) -> _FittedLogisticRegression:
        """Train on one label per row.

        Raises:
            ValueError: If there are fewer than two distinct labels.
        """
        if len(set(labels)) < 2:
            raise ValueError("logistic regression needs at least two distinct labels")
        model = LogisticRegression(C=_REGULARISATION_STRENGTH, max_iter=_MAX_ITERATIONS)
        with warnings.catch_warnings():
            # At 1 example per category every label is unique; sklearn warns that this
            # "could represent a regression problem". Here it is intended.
            warnings.filterwarnings("ignore", message="The number of unique classes")
            model.fit(vectors, list(labels))
        return _FittedLogisticRegression(model)
