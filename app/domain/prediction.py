"""One method's answer for one test message."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Prediction:
    """A method's guess for a test message, with what it cost to produce."""

    text: str
    true_label: str
    predicted_label: str
    latency_ms: float
    input_tokens: int = 0

    @property
    def is_correct(self) -> bool:
        """Return whether the guess matches the human label."""
        return self.predicted_label == self.true_label
