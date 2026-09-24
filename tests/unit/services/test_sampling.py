from collections import Counter

import pytest

from app.domain.errors.dataset_error import DatasetError
from app.domain.labeled_message import LabeledMessage
from app.services.sampling import draw_example_pools, sample_test_set, take_examples
from tests.conftest import make_messages


def _dataset() -> list[LabeledMessage]:
    return make_messages("alpha_intent", 10) + make_messages("beta_intent", 12)


def test_sample_test_set_draws_exactly_per_label_from_each_label() -> None:
    sampled = sample_test_set(_dataset(), per_label=4, seed=7)

    assert Counter(m.label for m in sampled) == {"alpha_intent": 4, "beta_intent": 4}


def test_sample_test_set_with_same_seed_is_identical() -> None:
    first = sample_test_set(_dataset(), per_label=4, seed=7)
    second = sample_test_set(_dataset(), per_label=4, seed=7)

    assert first == second


def test_sample_test_set_when_label_too_small_raises() -> None:
    with pytest.raises(DatasetError, match="alpha_intent"):
        sample_test_set(_dataset(), per_label=11, seed=7)


def test_take_examples_prefixes_are_nested_across_sizes() -> None:
    pools = draw_example_pools(_dataset(), max_per_label=6, seed=3)

    small = take_examples(pools, 2)
    large = take_examples(pools, 5)

    assert set(small) <= set(large)
    assert Counter(m.label for m in large) == {"alpha_intent": 5, "beta_intent": 5}


def test_draw_example_pools_differs_between_seeds() -> None:
    first = draw_example_pools(_dataset(), max_per_label=6, seed=1)
    second = draw_example_pools(_dataset(), max_per_label=6, seed=2)

    assert first != second


def test_draw_example_pools_when_label_too_small_raises() -> None:
    with pytest.raises(DatasetError):
        draw_example_pools(_dataset(), max_per_label=11, seed=1)
