from pathlib import Path

import pytest

from app import main as cli
from app.core.settings import BenchmarkSettings
from app.domain.benchmark_inputs import BenchmarkInputs
from app.domain.benchmark_method import BenchmarkMethod
from app.domain.errors.configuration_error import ConfigurationError
from app.domain.method_run import MethodRun
from app.repositories.results_repository import ResultsRepository
from tests.conftest import make_catalog, make_result


def _use_settings(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    def fake_settings() -> BenchmarkSettings:
        return BenchmarkSettings(  # type: ignore[call-arg]  # pydantic-settings init kwarg
            _env_file=None, results_dir=tmp_path / "results", data_dir=tmp_path / "data"
        )

    monkeypatch.setattr(cli, "BenchmarkSettings", fake_settings)


def test_build_parser_knows_every_command() -> None:
    parser = cli.build_parser()

    arguments = parser.parse_args(["run-jev", "--limit", "5", "--dry-run"])

    assert (arguments.command, arguments.limit, arguments.dry_run) == ("run-jev", 5, True)


def test_main_report_without_cosine_results_fails_cleanly(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _use_settings(monkeypatch, tmp_path)

    exit_code = cli.main(["report"])

    assert exit_code == 1
    assert "run-cosine" in capsys.readouterr().err


def test_main_run_jev_without_route_explains_what_to_set(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _use_settings(monkeypatch, tmp_path)

    exit_code = cli.main(["run-jev", "--dry-run"])

    assert exit_code == 1
    assert "JEV_API_KEY" in capsys.readouterr().err


def test_main_report_writes_markdown_and_chart(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _use_settings(monkeypatch, tmp_path)
    repository = ResultsRepository(tmp_path / "results")
    description = make_result(
        BenchmarkMethod.COSINE_DESCRIPTIONS, examples_per_label=0, seed=None, accuracy=0.7
    )
    repository.save_runs(
        "cosine", [MethodRun(description, ()), MethodRun(make_result(accuracy=0.8), ())]
    )

    exit_code = cli.main(["report"])

    assert exit_code == 0
    assert (tmp_path / "results" / "REPORT.md").exists()
    assert (tmp_path / "results" / "accuracy_vs_examples.png").exists()


def test_main_unexpected_error_returns_crash_code(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _use_settings(monkeypatch, tmp_path)

    def explode(_settings: BenchmarkSettings, _arguments: object) -> int:
        raise RuntimeError("boom")

    monkeypatch.setitem(cli._COMMANDS, "report", explode)  # noqa: SLF001 - CLI dispatch table

    assert cli.main(["report"]) == 2


def test_main_with_misspelled_env_key_fails_without_echoing_its_value(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("JEV_APIKEY=vck_SECRET_TYPO_123\n", encoding="utf-8")

    exit_code = cli.main(["report"])

    error = capsys.readouterr().err
    assert exit_code == 1
    assert "jev_apikey" in error
    assert "vck_SECRET_TYPO_123" not in error


def test_build_parser_has_cross_encoder_command_with_limit() -> None:
    arguments = cli.build_parser().parse_args(["run-cross-encoder", "--limit", "249"])

    assert (arguments.command, arguments.limit) == ("run-cross-encoder", 249)


def test_main_report_includes_cross_encoder_results_when_present(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _use_settings(monkeypatch, tmp_path)
    repository = ResultsRepository(tmp_path / "results")
    description = make_result(
        BenchmarkMethod.COSINE_DESCRIPTIONS, examples_per_label=0, seed=None, accuracy=0.7
    )
    repository.save_runs("cosine", [MethodRun(description, ()), MethodRun(make_result(), ())])
    cross = make_result(
        BenchmarkMethod.CROSS_ENCODER_DESCRIPTIONS, examples_per_label=0, seed=None, accuracy=0.75
    )
    repository.save_runs("cross_encoder", [MethodRun(cross, ())])
    repository.save_metadata("cross_encoder", {"cross_encoder_model": "reranker@abc"})

    assert cli.main(["report"]) == 0

    report = (tmp_path / "results" / "REPORT.md").read_text(encoding="utf-8")
    assert "| D · cross-encoder vs descriptions |" in report
    assert "reranker@abc" in report


def test_build_parser_has_trained_classifier_command() -> None:
    arguments = cli.build_parser().parse_args(["run-trained"])

    assert (arguments.command, arguments.limit) == ("run-trained", None)


@pytest.mark.parametrize(
    ("argv", "expected"),
    [
        (["report"], "results"),
        (["report", "--limit", "249"], "results/first_249"),
        (["report", "--probe", "tricky.v1"], "results/probe_tricky.v1"),
        (["report", "--probe", "tricky.v1", "--limit", "5"], "results/probe_tricky.v1/first_5"),
    ],
)
def test_results_for_keeps_each_experiment_in_its_own_folder(
    tmp_path: Path, argv: list[str], expected: str
) -> None:
    # tmp_path, not the real results/ folder: path_for creates directories.
    settings = BenchmarkSettings(_env_file=None, results_dir=tmp_path / "results")  # type: ignore[call-arg]  # pydantic-settings init kwarg
    repository = cli._results_for(settings, cli.build_parser().parse_args(argv))  # noqa: SLF001 - folder layout is the contract

    assert repository.path_for("x.json").parent == (tmp_path / expected).resolve()


def test_jev_catalog_without_examples_is_the_plain_catalog() -> None:
    inputs = BenchmarkInputs(make_catalog(), [], [], 0)

    assert cli._jev_catalog(inputs, None) is inputs.catalog  # noqa: SLF001 - B+ catalog choice


@pytest.mark.parametrize("per_label", [0, 36])
def test_jev_catalog_rejects_out_of_range_example_counts(per_label: int) -> None:
    inputs = BenchmarkInputs(make_catalog(), [], [], 0)

    with pytest.raises(ConfigurationError, match="1 to 35"):
        cli._jev_catalog(inputs, per_label)  # noqa: SLF001 - B+ catalog choice


class _NoClient:
    def __enter__(self) -> "_NoClient":
        return self

    def __exit__(self, *_exc: object) -> None:
        return None


def _route_settings(tmp_path: Path) -> BenchmarkSettings:
    return BenchmarkSettings(  # type: ignore[call-arg]  # pydantic-settings init kwarg
        _env_file=None,
        results_dir=tmp_path / "results",
        jev_api_key="public",
        jev_base_url="https://opencode.ai/zen",
        jev_model="jev-1.13-free",
    )


@pytest.mark.parametrize(("tokens", "exit_code"), [(422, 0), (500, 1)])
def test_verify_route_saves_evidence_and_fails_on_mismatch(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, tokens: int, exit_code: int
) -> None:
    monkeypatch.setattr(cli, "BenchmarkSettings", lambda: _route_settings(tmp_path))
    monkeypatch.setattr(cli, "create_typesafe_client", lambda **_kwargs: _NoClient())
    reference = cli.load_reference_cases(Path("fingerprints/typesafe_reference.v2.json"))[0]
    body = {**reference.reference_response, "usage": {"input_tokens": tokens, "output_tokens": 69}}

    class _FakeCaller:
        def __init__(self, _client: object, *, model: str) -> None:
            self.model = model

        def call(self, _state: object, _questions: object) -> dict[str, object]:
            return body

    monkeypatch.setattr(cli, "TypeSafeRawCaller", _FakeCaller)

    assert cli.main(["verify-route", "--max-cases", "1"]) == exit_code
    evidence = list((tmp_path / "results" / "route_verification").glob("*.json"))
    assert len(evidence) == 1
