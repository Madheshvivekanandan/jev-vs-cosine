"""Save and load benchmark results under the results directory."""

import json
import re
from collections.abc import Mapping, Sequence
from decimal import Decimal
from pathlib import Path
from typing import Final

from pydantic import BaseModel, ConfigDict, TypeAdapter, ValidationError

from app.domain.benchmark_method import BenchmarkMethod
from app.domain.errors.dataset_error import DatasetError
from app.domain.method_result import MethodResult
from app.domain.method_run import MethodRun
from app.domain.prediction import Prediction

_RESULT_SET_NAME: Final = re.compile(r"^[a-z][a-z0-9_]*$")
_METADATA: Final = TypeAdapter(dict[str, str])


class _MethodResultRecord(BaseModel):
    """JSON shape of one MethodResult; Decimal cost is stored as a string."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    method: BenchmarkMethod
    examples_per_label: int
    seed: int | None
    correct: int
    total: int
    accuracy: float
    accuracy_ci_low: float
    accuracy_ci_high: float
    median_latency_ms: float
    p95_latency_ms: float
    input_tokens: int
    list_price_cost_usd: Decimal


class _PredictionRecord(BaseModel):
    """JSON shape of one saved Prediction (one line of a predictions file)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    text: str
    true_label: str
    predicted_label: str
    is_correct: bool
    latency_ms: float
    input_tokens: int
    confidence: float | None = None


class ResultsRepository:
    """Writes `<name>.json` summaries, per-message predictions, and report files."""

    def __init__(self, results_dir: Path) -> None:
        """Keep every file this repository writes inside `results_dir`."""
        self._results_dir = results_dir

    def save_runs(self, name: str, runs: Sequence[MethodRun]) -> Path:
        """Save the summaries of `runs` and their per-message predictions.

        Returns:
            Path of the summary JSON file.
        """
        summary_path = self.path_for(f"{_checked(name)}.json")
        records = [_MethodResultRecord.model_validate(_as_dict(run.result)) for run in runs]
        summary = [record.model_dump(mode="json") for record in records]
        summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", "utf-8")
        for run in runs:
            self._save_predictions(name, run)
        return summary_path

    def load_results(self, name: str) -> list[MethodResult]:
        """Return the saved summaries for `name`, or an empty list if never saved.

        Raises:
            DatasetError: If the file exists but is not valid results JSON.
        """
        path = self.path_for(f"{_checked(name)}.json")
        if not path.exists():
            return []
        try:
            raw_records = json.loads(path.read_text(encoding="utf-8"))
            records = [_MethodResultRecord.model_validate(item) for item in raw_records]
        except (json.JSONDecodeError, TypeError, ValidationError) as exc:
            raise DatasetError(f"{path} is not a valid results file") from exc
        return [MethodResult(**record.model_dump()) for record in records]

    def save_metadata(self, name: str, metadata: Mapping[str, str]) -> Path:
        """Save how a result set was produced (route, model, prompt version, price)."""
        path = self.path_for(f"{_checked(name)}.meta.json")
        path.write_text(json.dumps(dict(metadata), indent=2, sort_keys=True) + "\n", "utf-8")
        return path

    def load_metadata(self, name: str) -> dict[str, str]:
        """Return the saved provenance for `name`, or an empty dict if none was saved.

        Raises:
            DatasetError: If the file exists but is not a flat JSON object of strings.
        """
        path = self.path_for(f"{_checked(name)}.meta.json")
        if not path.exists():
            return {}
        try:
            return _METADATA.validate_json(path.read_text(encoding="utf-8"))
        except ValidationError as exc:
            raise DatasetError(f"{path} is not a valid metadata file") from exc

    def write_text(self, filename: str, content: str) -> Path:
        """Write a report file (e.g. REPORT.md) and return its path."""
        path = self.path_for(filename)
        path.write_text(content, encoding="utf-8")
        return path

    def path_for(self, filename: str) -> Path:
        """Return a path for `filename`, refusing anything that escapes the results dir.

        Raises:
            ValueError: If `filename` resolves outside the results directory.
        """
        base = self._results_dir.resolve()
        path = (base / filename).resolve()
        if not path.is_relative_to(base):
            raise ValueError(f"{filename!r} is outside the results directory")
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def load_predictions(
        self,
        name: str,
        method: BenchmarkMethod,
        *,
        examples_per_label: int,
        seed: int | None,
    ) -> list[Prediction]:
        """Return the saved per-message predictions of one run, or [] if never saved.

        Raises:
            DatasetError: If the file exists but a line is not a valid prediction.
        """
        path = self.path_for(_predictions_filename(name, method, examples_per_label, seed))
        if not path.exists():
            return []
        try:
            records = [
                _PredictionRecord.model_validate_json(line)
                for line in path.read_text(encoding="utf-8").splitlines()
            ]
        except ValidationError as exc:
            raise DatasetError(f"{path} is not a valid predictions file") from exc
        return [Prediction(**record.model_dump(exclude={"is_correct"})) for record in records]

    def _save_predictions(self, name: str, run: MethodRun) -> None:
        result = run.result
        filename = _predictions_filename(
            name, result.method, result.examples_per_label, result.seed
        )
        lines = [json.dumps(_prediction_record(p), sort_keys=True) for p in run.predictions]
        self.path_for(filename).write_text("\n".join(lines) + "\n", encoding="utf-8")


def _predictions_filename(
    name: str, method: BenchmarkMethod, examples_per_label: int, seed: int | None
) -> str:
    seed_part = f"_seed{seed}" if seed is not None else ""
    return f"predictions/{_checked(name)}/{method.value}_k{examples_per_label}{seed_part}.jsonl"


def _prediction_record(prediction: Prediction) -> dict[str, object]:
    record: dict[str, object] = {
        "text": prediction.text,
        "true_label": prediction.true_label,
        "predicted_label": prediction.predicted_label,
        "is_correct": prediction.is_correct,
        "latency_ms": round(prediction.latency_ms, 3),
        "input_tokens": prediction.input_tokens,
    }
    # Only methods that report a confidence get the key, so the other files stay unchanged.
    if prediction.confidence is not None:
        record["confidence"] = round(prediction.confidence, 6)
    return record


def _checked(name: str) -> str:
    if not _RESULT_SET_NAME.match(name):
        raise ValueError(f"invalid result set name {name!r}")
    return name


def _as_dict(result: MethodResult) -> dict[str, object]:
    return {field: getattr(result, field) for field in _MethodResultRecord.model_fields}
