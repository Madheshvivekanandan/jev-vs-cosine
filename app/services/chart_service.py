"""Render the benchmark chart: zero-shot methods beside learning curves.

Left panel: the methods that see only the category descriptions (A, D, Jev), as dots
with 95% confidence whiskers. Jev is blue and the others neutral grey, named on the axis.
Right panel: accuracy against past examples per category for C (orange) and E (aqua),
with Jev as a reference band. Blue, orange and aqua are dataviz reference-palette slots
1-3, validated all-pairs for light mode (worst CVD ΔE 9.2, normal-vision ΔE 24.0). Aqua
sits below 3:1 contrast on the surface, so every series is also direct-labelled and the
same numbers are in REPORT.md's table. Splitting into panels keeps each panel within the
three validated colours as methods are added.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import matplotlib as mpl
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.ticker import NullLocator, PercentFormatter

from app.domain.benchmark_method import BenchmarkMethod
from app.domain.benchmark_results import BenchmarkResults
from app.domain.method_result import MethodResult
from app.domain.seed_aggregate import SeedAggregate, aggregate_across_seeds

CHART_FILENAME: Final = "accuracy_vs_examples.png"

_SURFACE: Final = "#fcfcfb"
_INK_PRIMARY: Final = "#0b0b0b"
_INK_SECONDARY: Final = "#52514e"
_INK_MUTED: Final = "#898781"
_GRIDLINE: Final = "#e1e0d9"
_AXIS: Final = "#c3c2b7"
_JEV_BLUE: Final = "#2a78d6"
_EXAMPLES_ORANGE: Final = "#eb6834"
_TRAINED_AQUA: Final = "#1baf7a"
_FONT_STACK: Final = ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"]
_WASH_ALPHA: Final = 0.10
_LINE_WIDTH: Final = 2.0
_MARKER_SIZE: Final = 9.0
_CLOSE_LABELS: Final = 0.035


@dataclass(frozen=True, slots=True)
class _ZeroShotPoint:
    """One method in the left panel."""

    tick: str
    result: MethodResult
    color: str


def render_accuracy_chart(
    results: BenchmarkResults,
    output_path: Path,
    *,
    sample_label: str = "Banking77 intent routing",
) -> None:
    """Write the two-panel accuracy chart as a PNG."""
    description = next(r for r in results.cosine if r.method is BenchmarkMethod.COSINE_DESCRIPTIONS)
    examples = [r for r in results.cosine if r.method is BenchmarkMethod.COSINE_EXAMPLES]
    with mpl.rc_context({"font.family": "sans-serif", "font.sans-serif": _FONT_STACK}):
        figure = Figure(figsize=(11, 5.8), dpi=200, facecolor=_SURFACE)
        left, right = figure.subplots(1, 2, sharey=True, width_ratios=[1.2, 2.6])
        figure.subplots_adjust(top=0.84, wspace=0.12)
        _plot_zero_shot(left, _zero_shot_points(results, description))
        _plot_learning_curves(
            right,
            aggregate_across_seeds(examples),
            aggregate_across_seeds(list(results.trained)),
            results.jev,
        )
        _style_y_axis(left)
        _add_titles(figure, sample_label, description.total)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(output_path, facecolor=_SURFACE, bbox_inches="tight")


def _zero_shot_points(results: BenchmarkResults, description: MethodResult) -> list[_ZeroShotPoint]:
    points = [_ZeroShotPoint("A\ncosine", description, _INK_MUTED)]
    if results.cross_encoder is not None:
        points.append(_ZeroShotPoint("D\ncross-encoder", results.cross_encoder, _INK_MUTED))
    if results.jev is not None:
        points.append(_ZeroShotPoint("B\nJev", results.jev, _JEV_BLUE))
    return points


def _plot_zero_shot(axes: Axes, points: Sequence[_ZeroShotPoint]) -> None:
    _style_panel(axes, "No examples (descriptions only)")
    for index, point in enumerate(points):
        result = point.result
        axes.vlines(
            index,
            result.accuracy_ci_low,
            result.accuracy_ci_high,
            color=point.color,
            linewidth=_LINE_WIDTH,
        )
        axes.plot(
            [index],
            [result.accuracy],
            marker="o",
            markersize=_MARKER_SIZE,
            color=point.color,
            markeredgecolor=_SURFACE,
            markeredgewidth=2,
        )
        _direct_label(axes, index, result.accuracy, f"{result.accuracy:.1%}", offset=(9, -3))
    axes.set_xticks(range(len(points)), labels=[p.tick for p in points])
    axes.set_xlim(-0.6, len(points) - 0.2)


def _plot_learning_curves(
    axes: Axes,
    cosine: Sequence[SeedAggregate],
    trained: Sequence[SeedAggregate],
    jev_result: MethodResult | None,
) -> None:
    _style_panel(axes, "Learning from past examples")
    axes.set_xscale("log")
    ticks = [a.examples_per_label for a in cosine]
    axes.set_xticks(ticks, labels=[str(tick) for tick in ticks])
    axes.xaxis.set_minor_locator(NullLocator())
    axes.set_xlabel("Past examples per category", color=_INK_SECONDARY, fontsize=10)
    if jev_result is not None:
        _plot_jev_reference(axes, jev_result, left_edge=ticks[0])
    cosine_offset, trained_offset = _end_label_offsets(cosine, trained)
    _plot_curve(axes, cosine, _EXAMPLES_ORANGE, "C · cosine vs past examples", cosine_offset)
    if trained:
        _plot_curve(
            axes, trained, _TRAINED_AQUA, "E · classifier on the same examples", trained_offset
        )
    axes.legend(loc="lower right", frameon=False, labelcolor=_INK_SECONDARY, fontsize=9)


def _plot_curve(
    axes: Axes,
    aggregates: Sequence[SeedAggregate],
    color: str,
    legend: str,
    end_offset: tuple[float, float],
) -> None:
    xs = [a.examples_per_label for a in aggregates]
    axes.fill_between(
        xs,
        [a.min_accuracy for a in aggregates],
        [a.max_accuracy for a in aggregates],
        color=color,
        alpha=_WASH_ALPHA,
        linewidth=0,
    )
    axes.plot(
        xs,
        [a.mean_accuracy for a in aggregates],
        color=color,
        linewidth=_LINE_WIDTH,
        marker="o",
        markersize=_MARKER_SIZE,
        markeredgecolor=_SURFACE,
        markeredgewidth=2,
        solid_capstyle="round",
        label=f"{legend} (mean; band = range over 3 draws)",
    )
    last = aggregates[-1]
    text = f"{legend.split(' ')[0]} {last.mean_accuracy:.1%}"
    _direct_label(axes, last.examples_per_label, last.mean_accuracy, text, offset=end_offset)


def _end_label_offsets(
    cosine: Sequence[SeedAggregate], trained: Sequence[SeedAggregate]
) -> tuple[tuple[float, float], tuple[float, float]]:
    above, below = (8.0, 6.0), (8.0, -14.0)
    if not trained or abs(cosine[-1].mean_accuracy - trained[-1].mean_accuracy) >= _CLOSE_LABELS:
        return above, above
    # Close end values: push the higher label up and the lower one down so they never overlap.
    return (
        (above, below) if cosine[-1].mean_accuracy >= trained[-1].mean_accuracy else (below, above)
    )


def _plot_jev_reference(axes: Axes, jev_result: MethodResult, *, left_edge: int) -> None:
    axes.axhspan(
        jev_result.accuracy_ci_low,
        jev_result.accuracy_ci_high,
        color=_JEV_BLUE,
        alpha=_WASH_ALPHA,
        linewidth=0,
    )
    axes.axhline(
        jev_result.accuracy,
        color=_JEV_BLUE,
        linewidth=_LINE_WIDTH,
        solid_capstyle="round",
        label="B · Jev, no examples (band = 95% CI)",
    )
    text = f"Jev {jev_result.accuracy:.1%}"
    _direct_label(axes, left_edge, jev_result.accuracy, text, offset=(2, 6))


def _style_panel(axes: Axes, title: str) -> None:
    axes.set_facecolor(_SURFACE)
    axes.set_ylim(0, 1)
    axes.grid(axis="y", color=_GRIDLINE, linewidth=1, linestyle="-")
    axes.set_axisbelow(True)
    for side in ("top", "right", "left"):
        axes.spines[side].set_visible(False)
    axes.spines["bottom"].set_color(_AXIS)
    axes.tick_params(colors=_INK_MUTED, length=0, labelsize=9)
    axes.set_title(title, loc="left", color=_INK_SECONDARY, fontsize=10)


def _style_y_axis(axes: Axes) -> None:
    axes.yaxis.set_major_formatter(PercentFormatter(xmax=1, decimals=0))
    axes.set_ylabel("Accuracy", color=_INK_SECONDARY, fontsize=10)


def _direct_label(
    axes: Axes, x: float, y: float, text: str, *, offset: tuple[float, float]
) -> None:
    axes.annotate(
        text,
        xy=(x, y),
        xytext=offset,
        textcoords="offset points",
        color=_INK_PRIMARY,
        fontsize=9,
    )


def _add_titles(figure: Figure, sample_label: str, test_messages: int) -> None:
    figure.suptitle(
        "Do you need Jev, or is cosine similarity enough?",
        x=0.07,
        y=0.985,
        ha="left",
        color=_INK_PRIMARY,
        fontsize=13,
        fontweight="bold",
    )
    figure.text(
        0.07,
        0.912,
        f"{sample_label} · {test_messages:,} test messages · 77 categories",
        color=_INK_SECONDARY,
        fontsize=9.5,
    )
