"""Port for training a classifier on labelled embeddings."""

from collections.abc import Sequence
from typing import Protocol

from app.services.ports.fitted_classifier import FittedClassifier
from app.services.vector_types import FloatMatrix


class ClassifierTrainer(Protocol):
    """Anything that learns labels from embedding rows."""

    def fit(self, vectors: FloatMatrix, labels: Sequence[str]) -> FittedClassifier:
        """Train on one label per row and return the fitted model."""
        ...
