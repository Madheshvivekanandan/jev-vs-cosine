import hashlib
from pathlib import Path
from types import MappingProxyType

import pytest

from app.domain.dataset_split import DatasetSplit
from app.domain.errors.dataset_error import DatasetError
from app.domain.labeled_message import LabeledMessage
from app.repositories.banking77_repository import Banking77Repository, fetch_https

_TRAIN = (
    b'text,category\n"Card never came, help",card_arrival\nHow do I top up?,topping_up_by_card\n'
)
_TEST = b"text,category\nWhere is my card?,card_arrival\n"


def _repository(tmp_path: Path, fetched: list[str]) -> Banking77Repository:
    bodies = {"train.csv": _TRAIN, "test.csv": _TEST}

    def fake_fetch(url: str) -> bytes:
        fetched.append(url)
        return bodies[url.rsplit("/", 1)[1]]

    checksums = MappingProxyType(
        {
            DatasetSplit.TRAIN: hashlib.sha256(_TRAIN).hexdigest(),
            DatasetSplit.TEST: hashlib.sha256(_TEST).hexdigest(),
        }
    )
    return Banking77Repository(tmp_path, fake_fetch, checksums=checksums)


def test_ensure_downloaded_fetches_pinned_commit_once(tmp_path: Path) -> None:
    fetched: list[str] = []
    repository = _repository(tmp_path, fetched)

    repository.ensure_downloaded()
    repository.ensure_downloaded()

    assert len(fetched) == 2
    assert all("57ec275d8078af65b7731c2a98be812d844a6d6b" in url for url in fetched)


def test_load_parses_quoted_commas(tmp_path: Path) -> None:
    repository = _repository(tmp_path, [])
    repository.ensure_downloaded()

    messages = repository.load(DatasetSplit.TRAIN)

    assert messages[0] == LabeledMessage("Card never came, help", "card_arrival")
    assert len(messages) == 2


def test_load_when_file_was_tampered_with_raises(tmp_path: Path) -> None:
    repository = _repository(tmp_path, [])
    repository.ensure_downloaded()
    (tmp_path / "banking77" / "test.csv").write_bytes(_TEST + b"extra,row\n")

    with pytest.raises(DatasetError, match="checksum"):
        repository.load(DatasetSplit.TEST)


def test_load_before_download_raises(tmp_path: Path) -> None:
    with pytest.raises(DatasetError, match="not found"):
        _repository(tmp_path, []).load(DatasetSplit.TEST)


@pytest.mark.parametrize(
    ("content", "message"),
    [
        (b"sentence,label\nhi,a\n", "header"),
        (b"text,category\n,card_arrival\n", "malformed"),
        (b"text,category\n", "no rows"),
    ],
)
def test_load_rejects_malformed_files(tmp_path: Path, content: bytes, message: str) -> None:
    checksums = MappingProxyType(
        {split: hashlib.sha256(content).hexdigest() for split in DatasetSplit}
    )
    repository = Banking77Repository(tmp_path, lambda _url: content, checksums=checksums)
    repository.ensure_downloaded()

    with pytest.raises(DatasetError, match=message):
        repository.load(DatasetSplit.TEST)


def test_ensure_downloaded_when_download_is_corrupt_raises(tmp_path: Path) -> None:
    repository = Banking77Repository(tmp_path, lambda _url: b"garbage")

    with pytest.raises(DatasetError, match="checksum"):
        repository.ensure_downloaded()


def test_fetch_https_rejects_plain_http() -> None:
    with pytest.raises(ValueError, match="https"):
        fetch_https("http://example.com/data.csv")
