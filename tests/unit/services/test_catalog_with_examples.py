import pytest

from app.domain.intent_catalog import IntentCatalog
from app.domain.labeled_message import LabeledMessage
from app.services.catalog_with_examples import catalog_with_examples
from tests.conftest import make_messages


def _pools() -> dict[str, list[LabeledMessage]]:
    return {
        "alpha_intent": make_messages("alpha_intent", 3),
        "beta_intent": make_messages("beta_intent", 3),
    }


def test_catalog_with_examples_appends_the_first_n_pool_messages(catalog: IntentCatalog) -> None:
    augmented = catalog_with_examples(catalog, _pools(), per_label=2, seed=1)

    assert augmented.descriptions["alpha_intent"] == (
        'about alpha. Example customer messages: "alpha message 0" | "alpha message 1"'
    )
    assert augmented.labels == catalog.labels
    assert augmented.instructions == catalog.instructions


def test_catalog_with_examples_gets_its_own_version_and_fingerprint(
    catalog: IntentCatalog,
) -> None:
    augmented = catalog_with_examples(catalog, _pools(), per_label=2, seed=1)

    assert augmented.version == "test.v1+examples2_seed1"
    assert augmented.fingerprint() != catalog.fingerprint()


def test_catalog_with_examples_needs_a_pool_for_every_label(catalog: IntentCatalog) -> None:
    with pytest.raises(KeyError):
        catalog_with_examples(
            catalog, {"alpha_intent": make_messages("alpha_intent", 2)}, per_label=1, seed=1
        )
