from decimal import Decimal
from pathlib import Path

import pytest

from app.domain.benchmark_method import BenchmarkMethod
from app.domain.method_result import MethodResult
from app.domain.report_context import ReportContext
from app.domain.seed_aggregate import aggregate_across_seeds
from app.services.chart_service import render_accuracy_chart
from app.services.report_builder import build_markdown_report, find_crossover
from tests.conftest import make_result


def _cosine_results() -> list[MethodResult]:
    return [
        make_result(
            BenchmarkMethod.COSINE_DESCRIPTIONS, examples_per_label=0, seed=None, accuracy=0.7
        ),
        make_result(examples_per_label=5, seed=1, accuracy=0.78),
        make_result(examples_per_label=5, seed=2, accuracy=0.80),
        make_result(examples_per_label=20, seed=1, accuracy=0.9),
        make_result(examples_per_label=20, seed=2, accuracy=0.88),
    ]


def _jev(accuracy: float = 0.85) -> MethodResult:
    return make_result(BenchmarkMethod.JEV, examples_per_label=0, seed=None, accuracy=accuracy)


def _context(
    *, jev_route: str | None = "`opencode.ai/jev-1.13-free`", jev_catalog: str | None = "cat.v1"
) -> ReportContext:
    return ReportContext(
        embedding_model="bge@abc",
        catalog_version="cat.v1",
        train_duplicates_removed=7,
        jev_route=jev_route,
        jev_catalog_version=jev_catalog,
        price_usd_per_million_tokens=Decimal("0.042"),
    )


def test_find_crossover_returns_first_setting_that_matches_jev() -> None:
    aggregates = aggregate_across_seeds(_cosine_results()[1:])

    assert find_crossover(aggregates, 0.85) == 20
    assert find_crossover(aggregates, 0.95) is None


def test_report_with_jev_states_gap_and_crossover() -> None:
    report = build_markdown_report(_cosine_results(), _jev(), _context())

    assert "Jev leads cosine by 15.0 points" in report
    assert "reaches Jev is 20 examples per category" in report
    assert "| B · Jev |" in report
    assert "accuracy_vs_examples.png" in report


def test_report_when_jev_is_below_method_a_does_not_claim_a_catch_up() -> None:
    report = build_markdown_report(_cosine_results(), _jev(0.65), _context())

    assert "already matches or beats Jev (70.0% vs 65.0%)" in report
    assert "reaches Jev" not in report


def test_report_without_jev_says_so() -> None:
    report = build_markdown_report(
        _cosine_results(), None, _context(jev_route=None, jev_catalog=None)
    )

    assert "has not been run yet" in report
    assert "| B · Jev |" not in report
    assert "Jev: not run" in report


def test_report_when_jev_never_catches_up() -> None:
    report = build_markdown_report(_cosine_results(), _jev(0.99), _context())

    assert "does not reach Jev within the tested range" in report


def test_report_notes_come_from_the_saved_context() -> None:
    report = build_markdown_report(_cosine_results(), _jev(), _context())

    assert "`cat.v1`" in report
    assert "opencode.ai/jev-1.13-free" in report
    assert "$0.042 per million" in report
    assert "7 training rows" in report
    assert "Warning" not in report


def test_report_warns_when_jev_and_cosine_used_different_catalogs() -> None:
    report = build_markdown_report(_cosine_results(), _jev(), _context(jev_catalog="cat.v2"))

    assert "not like for like" in report


def test_report_without_method_a_raises() -> None:
    with pytest.raises(ValueError, match="exactly one"):
        build_markdown_report(_cosine_results()[1:], None, _context())


@pytest.mark.parametrize("with_jev", [True, False])
def test_render_accuracy_chart_writes_png(tmp_path: Path, *, with_jev: bool) -> None:
    output = tmp_path / "chart.png"

    render_accuracy_chart(_cosine_results(), _jev() if with_jev else None, output)

    assert output.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
