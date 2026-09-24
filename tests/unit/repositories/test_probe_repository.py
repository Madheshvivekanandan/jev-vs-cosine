import json
from pathlib import Path

import pytest

from app.domain.errors.dataset_error import DatasetError
from app.domain.labeled_message import LabeledMessage
from app.repositories.probe_repository import ProbeRepository

_PROJECT_PROBES = Path(__file__).resolve().parents[3] / "probes"


def _write(tmp_path: Path, name: str, lines: list[str]) -> ProbeRepository:
    (tmp_path / f"{name}.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return ProbeRepository(tmp_path)


def test_load_reads_messages_and_ignores_documentation_fields(tmp_path: Path) -> None:
    line = json.dumps({"text": "hi", "label": "a", "trap_type": "negation", "rationale": "r"})
    repository = _write(tmp_path, "tricky.v1", [line, ""])

    assert repository.load("tricky.v1") == [LabeledMessage("hi", "a")]


@pytest.mark.parametrize("name", ["../secrets.v1", "Tricky.v1", "tricky", "tricky.v1.jsonl"])
def test_load_rejects_invalid_names(tmp_path: Path, name: str) -> None:
    with pytest.raises(DatasetError, match="invalid probe name"):
        ProbeRepository(tmp_path).load(name)


def test_load_when_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(DatasetError, match="not found"):
        ProbeRepository(tmp_path).load("absent.v1")


@pytest.mark.parametrize(
    ("lines", "message"),
    [
        ([json.dumps({"text": "hi"})], "line 1"),
        ([json.dumps({"text": "hi", "label": "a", "x": 1})], "line 1"),
        ([""], "no items"),
    ],
)
def test_load_rejects_malformed_files(tmp_path: Path, lines: list[str], message: str) -> None:
    repository = _write(tmp_path, "bad.v1", lines)

    with pytest.raises(DatasetError, match=message):
        repository.load("bad.v1")


@pytest.mark.parametrize(
    ("name", "count"),
    [("tricky.v1", 105), ("hinglish.v1", 144), ("tanglish.v1", 144), ("english_source.v1", 144)],
)
def test_shipped_probes_load(name: str, count: int) -> None:
    assert len(ProbeRepository(_PROJECT_PROBES).load(name)) == count
