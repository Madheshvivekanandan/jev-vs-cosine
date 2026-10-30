"""What happens if a method's answers are trusted only above a confidence threshold."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ThresholdOutcome:
    """Answers at or above `threshold` are routed automatically; the rest go to a person."""

    threshold: float
    total: int
    routed: int
    routed_correct: int

    @property
    def routed_share(self) -> float:
        """Return the fraction of all messages routed automatically."""
        return self.routed / self.total if self.total else 0.0

    @property
    def routed_accuracy(self) -> float:
        """Return the accuracy of the routed answers (0.0 when none are routed)."""
        return self.routed_correct / self.routed if self.routed else 0.0

    @property
    def routed_wrong(self) -> int:
        """Return how many wrong answers would be routed without a person seeing them."""
        return self.routed - self.routed_correct
