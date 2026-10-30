"""Port for a trained classifier that labels embeddings."""

from typing import Protocol

from app.services.vector_types import FloatMatrix


class FittedClassifier(Protocol):
    """A model already trained on labelled embeddings."""

    def predict(self, vectors: FloatMatrix) -> list[tuple[str, float]]:
        """Return one (predicted label, the model's probability for it) pair per row."""
        ...
