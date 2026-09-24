import dataclasses
import json
from decimal import Decimal
from pathlib import Path

import pytest

from app.domain.benchmark_method import BenchmarkMethod
from app.domain.errors.dataset_error import DatasetError
from app.domain.method_run import MethodRun
from app.domain.prediction import Prediction
from app.repositories.results_repository import ResultsRepository
from tests.conftest import make_result


def _run(seed: int | None = 1) -> MethodRun:
    prediction = Prediction("hi", "a", "b", 12.3456, 7)
    result = make_result(examples_per_label=5, seed=seed)
    return MethodRun(result, (prediction,))


def test_save_then_load_round_trips_results(tmp_path: Path) -> None:
    repository = ResultsRepository(tmp_path)
    jev_run = MethodRun(make_result(BenchmarkMethod.JEV, examples_per_label=0, seed=None), ())
    original = [_run(), jev_run]

    repository.save_runs("cosine", original)

    assert repository.load_results("cosine") == [run.result for run in original]


def test_save_runs_writes_predictions_per_configuration(tmp_path: Path) -> None:
    ResultsRepository(tmp_path).save_runs("cosine", [_run(seed=2)])

    lines = (tmp_path / "predictions/cosine/C_cosine_examples_k5_seed2.jsonl").read_text()
    record = json.loads(lines.splitlines()[0])

    assert record == {
        "input_tokens": 7,
        "is_correct": False,
        "latency_ms": 12.346,
        "predicted_label": "b",
        "text": "hi",
        "true_label": "a",
    }


def test_decimal_cost_survives_json_exactly(tmp_path: Path) -> None:
    repository = ResultsRepository(tmp_path)
    costly = dataclasses.replace(make_result(), list_price_cost_usd=Decimal("0.0841"))

    repository.save_runs("jev", [MethodRun(costly, ())])

    assert repository.load_results("jev")[0].list_price_cost_usd == Decimal("0.0841")


def test_load_results_when_never_saved_is_empty(tmp_path: Path) -> None:
    assert ResultsRepository(tmp_path).load_results("jev") == []


def test_load_results_when_corrupt_raises(tmp_path: Path) -> None:
    (tmp_path / "jev.json").write_text("[{}]", encoding="utf-8")

    with pytest.raises(DatasetError, match="not a valid"):
        ResultsRepository(tmp_path).load_results("jev")


@pytest.mark.parametrize("name", ["../escape", "Upper", ""])
def test_invalid_result_set_names_are_rejected(tmp_path: Path, name: str) -> None:
    with pytest.raises(ValueError, match="invalid"):
        ResultsRepository(tmp_path).load_results(name)


def test_path_for_refuses_to_escape_results_dir(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="outside"):
        ResultsRepository(tmp_path / "results").path_for("../secrets.txt")


def test_write_text_returns_path_inside_results_dir(tmp_path: Path) -> None:
    path = ResultsRepository(tmp_path).write_text("REPORT.md", "# hi\n")

    assert path.read_text(encoding="utf-8") == "# hi\n"
    assert path.parent == tmp_path.resolve()


def test_metadata_round_trips(tmp_path: Path) -> None:
    repository = ResultsRepository(tmp_path)

    repository.save_metadata("jev", {"route_id": "opencode.ai/jev-1.13-free"})

    assert repository.load_metadata("jev") == {"route_id": "opencode.ai/jev-1.13-free"}
    assert repository.load_metadata("cosine") == {}


def test_invalid_metadata_raises(tmp_path: Path) -> None:
    (tmp_path / "jev.meta.json").write_text('{"count": 3}', encoding="utf-8")

    with pytest.raises(DatasetError, match="metadata"):
        ResultsRepository(tmp_path).load_metadata("jev")
