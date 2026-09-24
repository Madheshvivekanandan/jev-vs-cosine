import dataclasses
from decimal import Decimal
from pathlib import Path

import pytest

from app.domain.benchmark_method import BenchmarkMethod
from app.domain.benchmark_results import BenchmarkResults
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
        cross_encoder_model=None,
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
    report = build_markdown_report(BenchmarkResults(_cosine_results(), jev=_jev()), _context())

    assert "Jev leads cosine by 15.0 points" in report
    assert "reaches Jev is 20 examples per category" in report
    assert "| B · Jev |" in report
    assert "accuracy_vs_examples.png" in report


def test_report_when_jev_is_below_method_a_does_not_claim_a_catch_up() -> None:
    report = build_markdown_report(BenchmarkResults(_cosine_results(), jev=_jev(0.65)), _context())

    assert "already matches or beats Jev (70.0% vs 65.0%)" in report
    assert "reaches Jev" not in report


def test_report_without_jev_says_so() -> None:
    report = build_markdown_report(
        BenchmarkResults(_cosine_results(), jev=None), _context(jev_route=None, jev_catalog=None)
    )

    assert "has not been run yet" in report
    assert "| B · Jev |" not in report
    assert "Jev: not run" in report


def test_report_when_jev_never_catches_up() -> None:
    report = build_markdown_report(BenchmarkResults(_cosine_results(), jev=_jev(0.99)), _context())

    assert "does not reach Jev within the tested range" in report


def test_report_notes_come_from_the_saved_context() -> None:
    report = build_markdown_report(BenchmarkResults(_cosine_results(), jev=_jev()), _context())

    assert "`cat.v1`" in report
    assert "opencode.ai/jev-1.13-free" in report
    assert "$0.042 per million" in report
    assert "7 training rows" in report
    assert "Warning" not in report


def test_report_warns_when_jev_and_cosine_used_different_catalogs() -> None:
    report = build_markdown_report(
        BenchmarkResults(_cosine_results(), jev=_jev()), _context(jev_catalog="cat.v2")
    )

    assert "not like for like" in report


def test_report_without_method_a_raises() -> None:
    with pytest.raises(ValueError, match="exactly one"):
        build_markdown_report(BenchmarkResults(_cosine_results()[1:], jev=None), _context())


@pytest.mark.parametrize("with_jev", [True, False])
def test_render_accuracy_chart_writes_png(tmp_path: Path, *, with_jev: bool) -> None:
    output = tmp_path / "chart.png"

    render_accuracy_chart(
        BenchmarkResults(_cosine_results(), jev=_jev() if with_jev else None), output
    )

    assert output.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


def _cross(accuracy: float) -> MethodResult:
    return make_result(
        BenchmarkMethod.CROSS_ENCODER_DESCRIPTIONS,
        examples_per_label=0,
        seed=None,
        accuracy=accuracy,
    )


def test_report_with_cross_encoder_compares_it_to_jev() -> None:
    report = build_markdown_report(
        BenchmarkResults(_cosine_results(), jev=_jev(0.85), cross_encoder=_cross(0.80)), _context()
    )

    assert "| D · cross-encoder vs descriptions |" in report
    assert "scores **80.0%**, -5.0 points vs Jev" in report


def test_report_with_cross_encoder_but_no_jev_compares_it_to_cosine() -> None:
    report = build_markdown_report(
        BenchmarkResults(_cosine_results(), cross_encoder=_cross(0.75)),
        _context(jev_route=None, jev_catalog=None),
    )

    assert "+5.0 points vs cosine vs descriptions" in report


@pytest.mark.parametrize("accuracy", [0.6, 0.9])
def test_render_accuracy_chart_with_cross_encoder_above_or_below_a(
    tmp_path: Path, accuracy: float
) -> None:
    output = tmp_path / "chart.png"

    render_accuracy_chart(
        BenchmarkResults(_cosine_results(), jev=_jev(), cross_encoder=_cross(accuracy)), output
    )

    assert output.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


def _trained(examples_per_label: int, accuracy: float) -> MethodResult:
    return make_result(
        BenchmarkMethod.TRAINED_CLASSIFIER,
        examples_per_label=examples_per_label,
        seed=1,
        accuracy=accuracy,
    )


def test_report_with_trained_classifier_rows_and_crossover() -> None:
    trained = [_trained(5, 0.86), _trained(20, 0.92)]
    report = build_markdown_report(
        BenchmarkResults(_cosine_results(), jev=_jev(0.85), trained=trained), _context()
    )

    assert "| E · classifier trained on past examples | 5 |" in report
    assert "reaches Jev at **5 examples per category**" in report


def test_report_with_trained_classifier_but_no_jev() -> None:
    report = build_markdown_report(
        BenchmarkResults(_cosine_results(), trained=[_trained(5, 0.8), _trained(20, 0.9)]),
        _context(jev_route=None, jev_catalog=None),
    )

    assert "reaches **90.0%** with 20 per category" in report


@pytest.mark.parametrize("trained_end", [0.9, 0.95])
def test_render_chart_with_all_methods(tmp_path: Path, trained_end: float) -> None:
    output = tmp_path / "chart.png"
    results = BenchmarkResults(
        _cosine_results(),
        jev=_jev(),
        cross_encoder=_cross(0.7),
        trained=[_trained(5, 0.8), _trained(20, trained_end)],
    )

    render_accuracy_chart(results, output)

    assert output.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


def test_report_for_a_probe_names_it_in_the_notes() -> None:
    context = dataclasses.replace(_context(), probe_name="tricky.v1")

    report = build_markdown_report(BenchmarkResults(_cosine_results(), jev=_jev()), context)

    assert "messages of probe `tricky.v1`" in report
    assert "13 per category" not in report
