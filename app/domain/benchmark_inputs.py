"""The loaded, validated inputs every benchmark command starts from."""

from dataclasses import dataclass

from app.domain.intent_catalog import IntentCatalog
from app.domain.labeled_message import LabeledMessage


@dataclass(frozen=True, slots=True)
class BenchmarkInputs:
    """Catalog, sampled test messages, and the training pool with test duplicates removed."""

    catalog: IntentCatalog
    test_set: list[LabeledMessage]
    train_set: list[LabeledMessage]
    train_duplicates_removed: int
