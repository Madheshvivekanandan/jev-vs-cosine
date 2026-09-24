"""Append-only on-disk cache of Jev answers, so no message is ever paid for twice."""

import json
import logging
from pathlib import Path

from pydantic import BaseModel, ConfigDict, ValidationError

from app.domain.errors.dataset_error import DatasetError
from app.domain.jev_decision import JevDecision

logger = logging.getLogger(__name__)


class _CacheRecord(BaseModel):
    """One JSON line in the cache file.

    `charged_tokens` is what the budget counted for the call: the reported usage, or the
    pre-flight estimate when the route reported none. Records written before this field
    existed have None and fall back to `input_tokens`.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    key: str
    choice: str
    confidence: float
    probabilities: dict[str, float]
    input_tokens: int | None
    model: str
    latency_ms: float
    charged_tokens: int | None = None


class JevDecisionCacheRepository:
    """Stores Jev decisions keyed by a hash of (route, catalog, message).

    The file is JSON Lines and only ever appended to, so an interrupted run loses at
    most the call in flight. Message text is not stored; the key is a hash.
    """

    def __init__(self, path: Path) -> None:
        """Open the cache, loading any decisions saved by earlier runs.

        Raises:
            DatasetError: If a complete line in the cache file is not a valid record.
        """
        self._path = path
        self._decisions: dict[str, JevDecision] = {}
        self._charged_tokens: dict[str, int] = {}
        self._load()

    def get(self, key: str) -> JevDecision | None:
        """Return the cached decision for `key`, or None if Jev was never asked."""
        return self._decisions.get(key)

    def charged_tokens(self, key: str) -> int:
        """Return the tokens the budget counted for `key` (0 if not cached)."""
        return self._charged_tokens.get(key, 0)

    def put(self, key: str, decision: JevDecision, *, charged_tokens: int) -> None:
        """Persist a new decision immediately, with the tokens the budget counted."""
        record = _CacheRecord(
            key=key,
            choice=decision.choice,
            confidence=decision.confidence,
            probabilities=dict(decision.probabilities),
            input_tokens=decision.input_tokens,
            model=decision.model,
            latency_ms=decision.latency_ms,
            charged_tokens=charged_tokens,
        )
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as cache_file:
            cache_file.write(json.dumps(record.model_dump(), sort_keys=True) + "\n")
        self._remember(record)

    def total_input_tokens(self) -> int:
        """Return tokens counted across every cached decision (reported or estimated)."""
        return sum(self._charged_tokens.values())

    def average_input_tokens(self) -> float | None:
        """Return mean reported input tokens per call, or None before any usage is known."""
        reported = [d.input_tokens for d in self._decisions.values() if d.input_tokens is not None]
        return sum(reported) / len(reported) if reported else None

    def _load(self) -> None:
        if not self._path.exists():
            return
        content = self._path.read_text(encoding="utf-8")
        lines = content.splitlines(keepends=True)
        for index, line in enumerate(lines):
            if not line.strip():
                continue
            is_unterminated_last = index == len(lines) - 1 and not line.endswith("\n")
            record = self._parse(line, index + 1, is_unterminated_last=is_unterminated_last)
            if record is None:
                self._drop_truncated_tail(content[: len(content) - len(line)])
            else:
                self._remember(record)

    def _drop_truncated_tail(self, intact_content: str) -> None:
        # Rewrite atomically without the partial line, so later appends stay parseable.
        temporary = self._path.with_name(self._path.name + ".tmp")
        temporary.write_text(intact_content, encoding="utf-8")
        temporary.replace(self._path)

    def _parse(
        self, line: str, line_number: int, *, is_unterminated_last: bool
    ) -> _CacheRecord | None:
        try:
            return _CacheRecord.model_validate_json(line)
        except ValidationError as exc:
            if is_unterminated_last:
                # A crash mid-write leaves a partial last line; that call is simply redone.
                logger.warning("jev_cache_truncated_line_dropped", extra={"line": line_number})
                return None
            raise DatasetError(f"{self._path} line {line_number} is not a valid record") from exc

    def _remember(self, record: _CacheRecord) -> None:
        self._decisions[record.key] = JevDecision(
            choice=record.choice,
            confidence=record.confidence,
            probabilities=record.probabilities,
            input_tokens=record.input_tokens,
            model=record.model,
            latency_ms=record.latency_ms,
        )
        charged = record.charged_tokens
        self._charged_tokens[record.key] = (
            charged if charged is not None else record.input_tokens or 0
        )
