"""Collapse method C's per-seed results into one point per examples-per-label setting."""

import statistics
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass

from app.domain.method_result import MethodResult


@dataclass(frozen=True, slots=True)
class SeedAggregate:
    """Mean and spread of accuracy across the random example draws at one setting."""

    examples_per_label: int
    mean_accuracy: float
    min_accuracy: float
    max_accuracy: float
    run_count: int


def aggregate_across_seeds(results: Sequence[MethodResult]) -> list[SeedAggregate]:
    """Group results by examples-per-label and summarise accuracy across seeds."""
    accuracies_by_setting: dict[int, list[float]] = defaultdict(list)
    for result in results:
        accuracies_by_setting[result.examples_per_label].append(result.accuracy)
    return [
        SeedAggregate(
            examples_per_label=setting,
            mean_accuracy=statistics.fmean(accuracies),
            min_accuracy=min(accuracies),
            max_accuracy=max(accuracies),
            run_count=len(accuracies),
        )
        for setting, accuracies in sorted(accuracies_by_setting.items())
    ]
