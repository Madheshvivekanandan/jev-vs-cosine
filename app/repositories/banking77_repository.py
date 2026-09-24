"""Download, verify and read the Banking77 CSV files."""

import csv
import hashlib
import io
import urllib.request
from collections.abc import Callable, Mapping
from pathlib import Path
from types import MappingProxyType
from typing import Final

from app.domain.dataset_split import DatasetSplit
from app.domain.errors.dataset_error import DatasetError
from app.domain.labeled_message import LabeledMessage

# Pinned to one upstream commit and verified by checksum, so every run grades the
# exact same messages even if the upstream repository changes.
DATASET_COMMIT: Final = "57ec275d8078af65b7731c2a98be812d844a6d6b"
_BASE_URL: Final = (
    "https://raw.githubusercontent.com/PolyAI-LDN/task-specific-datasets/"
    f"{DATASET_COMMIT}/banking_data"
)
EXPECTED_SHA256: Final[Mapping[DatasetSplit, str]] = MappingProxyType(
    {
        DatasetSplit.TRAIN: "b06e26ac675513959a63135f11b94ea7786ed02da65db93a5650d8838cbc664b",
        DatasetSplit.TEST: "d12d6e3bc4c3103966ae786dc435913c0c563dfa328f5a3646d0e62cfeeb474d",
    }
)
_EXPECTED_HEADER: Final = ["text", "category"]
_DOWNLOAD_TIMEOUT_SECONDS: Final = 30.0

type Fetcher = Callable[[str], bytes]


def fetch_https(url: str) -> bytes:
    """Return the body at an https URL.

    Raises:
        ValueError: If the URL is not https.
    """
    if not url.startswith("https://"):
        raise ValueError("only https downloads are allowed")
    # S310 is satisfied by the https check above; the URL is a module constant.
    with urllib.request.urlopen(url, timeout=_DOWNLOAD_TIMEOUT_SECONDS) as response:  # noqa: S310
        body: bytes = response.read()
    return body


class Banking77Repository:
    """Keeps verified copies of the Banking77 splits under `data_dir`."""

    def __init__(
        self,
        data_dir: Path,
        fetch: Fetcher,
        *,
        checksums: Mapping[DatasetSplit, str] = EXPECTED_SHA256,
    ) -> None:
        """Configure where files live, how to download them, and their expected hashes."""
        self._data_dir = data_dir
        self._fetch = fetch
        self._checksums = checksums

    def ensure_downloaded(self) -> None:
        """Download any split that is missing or corrupt.

        Raises:
            DatasetError: If a downloaded file does not match its pinned checksum.
        """
        for split in DatasetSplit:
            path = self._path(split)
            if path.exists() and self._is_intact(split, path.read_bytes()):
                continue
            content = self._fetch(f"{_BASE_URL}/{split.value}.csv")
            self._verify(split, content)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)

    def load(self, split: DatasetSplit) -> list[LabeledMessage]:
        """Return every message in a split, in file order.

        Raises:
            DatasetError: If the file is missing, fails its checksum, or is malformed.
        """
        path = self._path(split)
        if not path.exists():
            raise DatasetError(f"{path} not found; run the download command first")
        content = path.read_bytes()
        self._verify(split, content)
        return _parse(content.decode("utf-8"), path)

    def _path(self, split: DatasetSplit) -> Path:
        return self._data_dir / "banking77" / f"{split.value}.csv"

    def _is_intact(self, split: DatasetSplit, content: bytes) -> bool:
        return hashlib.sha256(content).hexdigest() == self._checksums[split]

    def _verify(self, split: DatasetSplit, content: bytes) -> None:
        if not self._is_intact(split, content):
            raise DatasetError(f"Banking77 {split.value} split does not match its checksum")


def _parse(text: str, path: Path) -> list[LabeledMessage]:
    reader = csv.reader(io.StringIO(text, newline=""))
    header = next(reader, None)
    if header != _EXPECTED_HEADER:
        raise DatasetError(f"{path} has header {header}, expected {_EXPECTED_HEADER}")
    messages: list[LabeledMessage] = []
    for line_number, row in enumerate(reader, start=2):
        if len(row) != len(_EXPECTED_HEADER) or not row[0].strip() or not row[1]:
            raise DatasetError(f"{path} row {line_number} is malformed")
        messages.append(LabeledMessage(text=row[0], label=row[1]))
    if not messages:
        raise DatasetError(f"{path} has no rows")
    return messages
