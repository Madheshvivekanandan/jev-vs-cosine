import json
from pathlib import Path

import pytest

from app.domain.errors.dataset_error import DatasetError
from app.domain.jev_decision import JevDecision
from app.repositories.jev_decision_cache_repository import JevDecisionCacheRepository


def _decision(tokens: int | None = 120) -> JevDecision:
    return JevDecision(
        choice="card_arrival",
        confidence=0.8,
        probabilities={"card_arrival": 0.9, "card_linking": 0.1},
        input_tokens=tokens,
        model="jev-1.13.0",
        latency_ms=210.5,
    )


def test_put_then_get_round_trips_across_instances(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "cache.jsonl"
    JevDecisionCacheRepository(path).put("k1", _decision(), charged_tokens=120)

    reopened = JevDecisionCacheRepository(path)

    assert reopened.get("k1") == _decision()
    assert reopened.charged_tokens("k1") == 120
    assert reopened.get("unknown") is None


def test_estimated_charges_survive_a_restart_when_usage_is_missing(tmp_path: Path) -> None:
    path = tmp_path / "cache.jsonl"
    cache = JevDecisionCacheRepository(path)
    cache.put("k1", _decision(100), charged_tokens=100)
    cache.put("k2", _decision(None), charged_tokens=2500)

    reopened = JevDecisionCacheRepository(path)

    assert reopened.total_input_tokens() == 2600
    assert reopened.average_input_tokens() == 100


def test_records_written_before_charged_tokens_existed_fall_back_to_usage(
    tmp_path: Path,
) -> None:
    path = tmp_path / "cache.jsonl"
    legacy = {
        "key": "old",
        "choice": "a",
        "confidence": 0.5,
        "probabilities": {"a": 1.0},
        "input_tokens": 300,
        "model": "m",
        "latency_ms": 1.0,
    }
    path.write_text(json.dumps(legacy) + "\n", encoding="utf-8")

    assert JevDecisionCacheRepository(path).total_input_tokens() == 300


def test_average_input_tokens_when_empty_is_none(tmp_path: Path) -> None:
    assert JevDecisionCacheRepository(tmp_path / "cache.jsonl").average_input_tokens() is None


def test_truncated_final_line_is_ignored_and_the_next_write_starts_a_new_line(
    tmp_path: Path,
) -> None:
    path = tmp_path / "cache.jsonl"
    JevDecisionCacheRepository(path).put("k1", _decision(), charged_tokens=120)
    with path.open("a", encoding="utf-8") as cache_file:
        cache_file.write('{"key": "k2", "choi')  # crash mid-write

    cache = JevDecisionCacheRepository(path)
    cache.put("k3", _decision(), charged_tokens=120)

    reopened = JevDecisionCacheRepository(path)
    assert reopened.get("k2") is None
    assert reopened.get("k3") is not None


def test_blank_lines_are_skipped(tmp_path: Path) -> None:
    path = tmp_path / "cache.jsonl"
    JevDecisionCacheRepository(path).put("k1", _decision(), charged_tokens=120)
    with path.open("a", encoding="utf-8") as cache_file:
        cache_file.write("\n\n")

    assert JevDecisionCacheRepository(path).get("k1") is not None


def test_corrupt_line_in_the_middle_raises_with_line_number(tmp_path: Path) -> None:
    path = tmp_path / "cache.jsonl"
    path.write_text('{"not": "a record"}\n', encoding="utf-8")

    with pytest.raises(DatasetError, match="line 1"):
        JevDecisionCacheRepository(path)
