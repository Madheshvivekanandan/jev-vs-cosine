"""Load probe sets: small, hand-built test sets stored as JSON Lines under probes/."""

import re
from pathlib import Path
from typing import Final

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.domain.errors.dataset_error import DatasetError
from app.domain.labeled_message import LabeledMessage

_PROBE_NAME: Final = re.compile(r"^[a-z][a-z0-9_]*\.v[0-9]+$")


class _ProbeRecord(BaseModel):
    """One line of a probe file. Extra fields document how the item was built."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    text: str = Field(min_length=1)
    label: str = Field(min_length=1)
    trap_type: str | None = None
    distractor_label: str | None = None
    rationale: str | None = None
    source_text: str | None = None


class ProbeRepository:
    """Reads `probes/<name>.jsonl`, e.g. `tricky.v1` or `hinglish.v1`."""

    def __init__(self, probes_dir: Path) -> None:
        """Keep every read inside `probes_dir`."""
        self._probes_dir = probes_dir

    def load(self, name: str) -> list[LabeledMessage]:
        """Return the probe's messages in file order.

        Raises:
            DatasetError: If the name is invalid, the file is missing, or a line is malformed.
        """
        path = self._path(name)
        messages: list[LabeledMessage] = []
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                record = _ProbeRecord.model_validate_json(line)
            except ValidationError as exc:
                raise DatasetError(f"{path} line {line_number} is not a valid probe item") from exc
            messages.append(LabeledMessage(text=record.text, label=record.label))
        if not messages:
            raise DatasetError(f"{path} has no items")
        return messages

    def _path(self, name: str) -> Path:
        if not _PROBE_NAME.match(name):
            raise DatasetError(f"invalid probe name {name!r}; expected e.g. 'tricky.v1'")
        base = self._probes_dir.resolve()
        path = (base / f"{name}.jsonl").resolve()
        if not path.is_relative_to(base) or not path.exists():
            raise DatasetError(f"probe {name!r} not found under {self._probes_dir}")
        return path
