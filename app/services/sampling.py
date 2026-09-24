"""Deterministic, stratified sampling of test messages and past-example pools."""

import random
from collections import defaultdict
from collections.abc import Mapping, Sequence

from app.domain.errors.dataset_error import DatasetError
from app.domain.labeled_message import LabeledMessage


def group_by_label(messages: Sequence[LabeledMessage]) -> dict[str, list[LabeledMessage]]:
    """Return messages grouped by label, keeping file order inside each group."""
    groups: dict[str, list[LabeledMessage]] = defaultdict(list)
    for message in messages:
        groups[message.label].append(message)
    return dict(groups)


def sample_test_set(
    messages: Sequence[LabeledMessage], *, per_label: int, seed: int
) -> list[LabeledMessage]:
    """Draw `per_label` messages from every label, then shuffle them.

    The final shuffle means a `--limit N` smoke run covers many labels, not one.

    Raises:
        DatasetError: If any label has fewer than `per_label` messages.
    """
    rng = random.Random(seed)  # noqa: S311 - reproducible sampling, not security
    sampled: list[LabeledMessage] = []
    for label, group in sorted(group_by_label(messages).items()):
        _ensure_enough(label, group, per_label)
        sampled.extend(rng.sample(group, per_label))
    rng.shuffle(sampled)
    return sampled


def draw_example_pools(
    messages: Sequence[LabeledMessage], *, max_per_label: int, seed: int
) -> dict[str, list[LabeledMessage]]:
    """Return a random ordering of `max_per_label` examples for every label.

    Taking a prefix of each pool gives nested example sets: the 5 examples used at
    5-per-label are also among the 10 used at 10-per-label, so the curve measures
    "more examples", not "different examples".

    Raises:
        DatasetError: If any label has fewer than `max_per_label` messages.
    """
    rng = random.Random(seed)  # noqa: S311 - reproducible sampling, not security
    pools: dict[str, list[LabeledMessage]] = {}
    for label, group in sorted(group_by_label(messages).items()):
        _ensure_enough(label, group, max_per_label)
        pools[label] = rng.sample(group, max_per_label)
    return pools


def take_examples(
    pools: Mapping[str, Sequence[LabeledMessage]], per_label: int
) -> list[LabeledMessage]:
    """Return the first `per_label` examples of every pool, labels in sorted order."""
    return [message for label in sorted(pools) for message in pools[label][:per_label]]


def _ensure_enough(label: str, group: Sequence[LabeledMessage], needed: int) -> None:
    if len(group) < needed:
        raise DatasetError(f"label {label!r} has {len(group)} messages; {needed} are needed")
