"""The fixed knobs of the experiment, in one place."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ExperimentDesign:
    """Sizes and seeds that define the benchmark.

    Defaults: 13 test messages per label gives 1,001 test messages (77 labels). The
    examples grid stops at 35 because the smallest Banking77 training label has 35 rows.
    Three seeds show how much method C depends on which examples happened to be drawn.
    """

    test_messages_per_label: int = 13
    test_sample_seed: int = 42
    examples_per_label_grid: tuple[int, ...] = (1, 5, 10, 20, 35)
    example_pool_seeds: tuple[int, ...] = (1, 2, 3)
    top_k_neighbours: int = 5

    @property
    def max_examples_per_label(self) -> int:
        """Return the largest examples-per-label setting in the grid."""
        return max(self.examples_per_label_grid)
