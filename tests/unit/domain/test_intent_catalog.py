import pytest

from app.domain.intent_catalog import IntentCatalog
from tests.conftest import make_catalog


def test_intent_catalog_when_empty_raises() -> None:
    with pytest.raises(ValueError, match="at least one"):
        IntentCatalog(version="v", instructions="q", descriptions={})


def test_intent_catalog_descriptions_cannot_be_mutated() -> None:
    catalog = make_catalog()

    with pytest.raises(TypeError):
        catalog.descriptions["new"] = "x"  # type: ignore[index]  # proving immutability


def test_embedding_text_combines_readable_label_and_description() -> None:
    catalog = make_catalog(["card_arrival"])

    assert catalog.embedding_text("card_arrival") == "card arrival: about card"


def test_fingerprint_changes_when_wording_changes() -> None:
    original = make_catalog()
    reworded = IntentCatalog(
        version=original.version,
        instructions=original.instructions + "?",
        descriptions=original.descriptions,
    )

    assert original.fingerprint() == make_catalog().fingerprint()
    assert original.fingerprint() != reworded.fingerprint()
