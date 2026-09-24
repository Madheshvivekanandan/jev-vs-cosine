import itertools
from collections.abc import Sequence

from app.domain.benchmark_method import BenchmarkMethod
from app.domain.experiment_design import ExperimentDesign
from app.services.trained_classifier_benchmark_service import TrainedClassifierBenchmarkService
from app.services.vector_types import FloatMatrix
from tests.conftest import KeywordEmbedder, make_messages

_DESIGN = ExperimentDesign(examples_per_label_grid=(1, 3), example_pool_seeds=(1, 2))


class _NearestKeywordClassifier:
    """Fake fitted model: the label whose keyword dimension is largest."""

    def __init__(self, labels_by_column: dict[int, str]) -> None:
        self._labels_by_column = labels_by_column

    def predict(self, vectors: FloatMatrix) -> list[str]:
        return [self._labels_by_column[int(row.argmax())] for row in vectors]


class _RecordingTrainer:
    def __init__(self) -> None:
        self.training_sizes: list[int] = []

    def fit(self, vectors: FloatMatrix, labels: Sequence[str]) -> _NearestKeywordClassifier:
        self.training_sizes.append(len(labels))
        columns = {int(row.argmax()): label for row, label in zip(vectors, labels, strict=True)}
        return _NearestKeywordClassifier(columns)


def test_run_trains_once_per_seed_and_size_on_nested_pools() -> None:
    trainer = _RecordingTrainer()
    ticks = itertools.count()
    service = TrainedClassifierBenchmarkService(
        KeywordEmbedder(["alpha", "beta"]), trainer, _DESIGN, clock=lambda: float(next(ticks))
    )
    test_set = make_messages("alpha_intent", 2) + make_messages("beta_intent", 2)
    train_set = make_messages("alpha_intent", 4) + make_messages("beta_intent", 4)

    runs = service.run(test_set, train_set)

    assert trainer.training_sizes == [2, 6, 2, 6]  # 2 labels x (1, 3) examples, per seed
    assert [(r.result.seed, r.result.examples_per_label) for r in runs] == [
        (1, 1),
        (1, 3),
        (2, 1),
        (2, 3),
    ]
    assert all(r.result.method is BenchmarkMethod.TRAINED_CLASSIFIER for r in runs)
    assert all(r.result.accuracy == 1.0 for r in runs)
