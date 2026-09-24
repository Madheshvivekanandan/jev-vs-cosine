import pytest

from app.domain.errors.configuration_error import ConfigurationError
from app.domain.intent_catalog import IntentCatalog
from app.domain.labeled_message import LabeledMessage
from app.services.dataset_checks import ensure_catalog_matches_dataset, remove_test_duplicates
from tests.conftest import make_messages


def test_ensure_catalog_matches_dataset_accepts_identical_labels(catalog: IntentCatalog) -> None:
    messages = make_messages("alpha_intent", 1) + make_messages("beta_intent", 1)

    ensure_catalog_matches_dataset(catalog, messages)


def test_ensure_catalog_matches_dataset_names_missing_and_unknown(catalog: IntentCatalog) -> None:
    messages = make_messages("alpha_intent", 1) + make_messages("gamma_intent", 1)

    with pytest.raises(ConfigurationError, match="gamma_intent") as caught:
        ensure_catalog_matches_dataset(catalog, messages)

    assert "beta_intent" in str(caught.value)


def test_remove_test_duplicates_ignores_case_and_whitespace() -> None:
    train = [
        LabeledMessage("\nMy PIN is blocked  ", "pin_blocked"),
        LabeledMessage("How do I top up?", "topping_up_by_card"),
    ]
    test = [LabeledMessage("my pin is blocked", "pin_blocked")]

    kept, removed = remove_test_duplicates(train, test)

    assert removed == 1
    assert kept == [train[1]]
