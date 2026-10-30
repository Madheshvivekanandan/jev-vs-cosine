"""Saved predictions that the triage report replays."""

from collections.abc import Mapping
from dataclasses import dataclass

from app.domain.prediction import Prediction

type RunsPerSeed = tuple[tuple[Prediction, ...], ...]


@dataclass(frozen=True, slots=True)
class TriageInputs:
    """Jev's predictions plus methods E and C, keyed by examples per category.

    Each value holds one prediction run per random draw of past examples, in the same
    seed order for `trained` and `voting`, so draw i of one pairs with draw i of the other.
    """

    jev: tuple[Prediction, ...]
    trained: Mapping[int, RunsPerSeed]
    voting: Mapping[int, RunsPerSeed]
