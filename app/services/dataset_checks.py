"""Guards on the dataset: catalog/label agreement and train/test separation."""

from collections.abc import Sequence

from app.domain.errors.configuration_error import ConfigurationError
from app.domain.intent_catalog import IntentCatalog
from app.domain.labeled_message import LabeledMessage


def ensure_catalog_matches_dataset(
    catalog: IntentCatalog, messages: Sequence[LabeledMessage]
) -> None:
    """Fail unless every dataset label has a description and every description a label.

    Raises:
        ConfigurationError: If the catalog and dataset label sets differ.
    """
    dataset_labels = {message.label for message in messages}
    catalog_labels = set(catalog.labels)
    missing = sorted(dataset_labels - catalog_labels)
    unknown = sorted(catalog_labels - dataset_labels)
    if missing or unknown:
        raise ConfigurationError(
            f"catalog {catalog.version} does not match the dataset: "
            f"missing descriptions for {missing}, unknown labels {unknown}"
        )


def remove_test_duplicates(
    train_set: Sequence[LabeledMessage], test_set: Sequence[LabeledMessage]
) -> tuple[list[LabeledMessage], int]:
    """Drop training rows whose text equals a test message, ignoring case and whitespace.

    Upstream Banking77 has a few such near-copies (e.g. a leading newline). Left in, one
    could be drawn as a "past example" for method C and score its own test twin.

    Returns:
        The kept training rows and how many were removed.
    """
    test_texts = {_normalise(message.text) for message in test_set}
    kept = [message for message in train_set if _normalise(message.text) not in test_texts]
    return kept, len(train_set) - len(kept)


def _normalise(text: str) -> str:
    return " ".join(text.lower().split())
