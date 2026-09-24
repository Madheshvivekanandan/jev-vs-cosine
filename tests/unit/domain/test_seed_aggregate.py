import pytest

from app.domain.seed_aggregate import aggregate_across_seeds
from tests.conftest import make_result


def test_aggregate_across_seeds_groups_by_setting_in_ascending_order() -> None:
    results = [
        make_result(examples_per_label=20, seed=1, accuracy=0.9),
        make_result(examples_per_label=5, seed=1, accuracy=0.7),
        make_result(examples_per_label=5, seed=2, accuracy=0.8),
    ]

    aggregates = aggregate_across_seeds(results)

    assert [a.examples_per_label for a in aggregates] == [5, 20]
    assert aggregates[0].mean_accuracy == pytest.approx(0.75)
    assert (aggregates[0].min_accuracy, aggregates[0].max_accuracy) == (0.7, 0.8)
    assert aggregates[0].run_count == 2


def test_aggregate_across_seeds_when_empty_returns_empty() -> None:
    assert aggregate_across_seeds([]) == []
