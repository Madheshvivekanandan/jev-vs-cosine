"""Score of a cheap-first cascade that asks Jev only for some messages."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CascadeOutcome:
    """How often the cascade was right, and how many messages it escalated to Jev."""

    total: int
    correct: int
    escalated: int

    @property
    def accuracy(self) -> float:
        """Return the fraction of messages the cascade answered correctly."""
        return self.correct / self.total if self.total else 0.0

    @property
    def escalated_share(self) -> float:
        """Return the fraction of messages sent to Jev."""
        return self.escalated / self.total if self.total else 0.0
