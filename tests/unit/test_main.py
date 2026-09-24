from pathlib import Path

import pytest

from app import main as cli
from app.core.settings import BenchmarkSettings
from app.domain.benchmark_method import BenchmarkMethod
from app.domain.method_run import MethodRun
from app.repositories.results_repository import ResultsRepository
from tests.conftest import make_result


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
