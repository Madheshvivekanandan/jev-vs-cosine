import json
from pathlib import Path

import pytest

from app.domain.errors.configuration_error import ConfigurationError
from app.repositories.intent_catalog_repository import load_intent_catalog

_PROJECT_CATALOG = Path(__file__).resolve().parents[3] / "prompts" / "banking77_intents.v1.json"


def _write(tmp_path: Path, payload: object) -> Path:
    path = tmp_path / "catalog.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_load_intent_catalog_reads_the_shipped_banking77_catalog() -> None:
    catalog = load_intent_catalog(_PROJECT_CATALOG)

    assert catalog.version == "banking77_intents.v1"
    assert len(catalog.labels) == 77
    assert "reverted_card_payment?" in catalog.labels


def test_load_intent_catalog_when_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError, match="not found"):
        load_intent_catalog(tmp_path / "missing.json")


@pytest.mark.parametrize(
    "payload",
    [
        {"version": "v", "instructions": "q", "descriptions": {}},
        {"version": "v", "instructions": "q", "descriptions": {"a": "x"}, "typo": 1},
        {"version": "v", "descriptions": {"a": "x"}},
    ],
)
def test_load_intent_catalog_rejects_invalid_shapes(tmp_path: Path, payload: object) -> None:
    with pytest.raises(ConfigurationError, match="invalid"):
        load_intent_catalog(_write(tmp_path, payload))


def test_load_intent_catalog_rejects_blank_description(tmp_path: Path) -> None:
    path = _write(tmp_path, {"version": "v", "instructions": "q", "descriptions": {"a": " "}})

    with pytest.raises(ConfigurationError, match="empty description"):
        load_intent_catalog(path)
