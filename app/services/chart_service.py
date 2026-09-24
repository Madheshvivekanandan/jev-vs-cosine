"""Render the one chart the benchmark exists to produce: accuracy vs examples per category.

Colours are dataviz reference-palette slots 1-3 plus violet (slot 7), the only fourth
colour that validated all-pairs for light mode (worst CVD ΔE 9.2, normal-vision ΔE 16.3).
Aqua sits below 3:1 contrast on the surface, so every series is also direct-labelled and
the same numbers are in REPORT.md's table.
"""

from collections.abc import Sequence
from pathlib import Path
from typing import Final

import matplotlib as mpl
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.ticker import PercentFormatter

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
_DESCRIPTIONS_AQUA: Final = "#1baf7a"
_CROSS_ENCODER_VIOLET: Final = "#4a3aa7"
_FONT_STACK: Final = ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"]
_WASH_ALPHA: Final = 0.10
_LINE_WIDTH: Final = 2.0
_MARKER_SIZE: Final = 9.0


def render_accuracy_chart(results: BenchmarkResults, output_path: Path) -> None:
    """Write the accuracy-vs-examples chart as a PNG."""
    jev_result, cross_encoder_result = results.jev, results.cross_encoder
    examples = [r for r in results.cosine if r.method is BenchmarkMethod.COSINE_EXAMPLES]
    description = next(r for r in results.cosine if r.method is BenchmarkMethod.COSINE_DESCRIPTIONS)
    aggregates = aggregate_across_seeds(examples)
    with mpl.rc_context({"font.family": "sans-serif", "font.sans-serif": _FONT_STACK}):
        figure = Figure(figsize=(9, 5.5), dpi=200, facecolor=_SURFACE)
        axes = figure.add_subplot()
        _style_axes(axes, aggregates)
        _plot_examples(axes, aggregates)
        _plot_descriptions(axes, description)
        if cross_encoder_result is not None:
            _plot_cross_encoder(axes, cross_encoder_result, above=description.accuracy)
        if jev_result is not None:
            _plot_jev(axes, jev_result, right_edge=aggregates[-1].examples_per_label)
        _add_titles(figure, description.total)
        axes.legend(loc="lower right", frameon=False, labelcolor=_INK_SECONDARY, fontsize=9)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(output_path, facecolor=_SURFACE, bbox_inches="tight")


def _style_axes(axes: Axes, aggregates: Sequence[SeedAggregate]) -> None:
    axes.set_facecolor(_SURFACE)
    # symlog: linear between 0 and 1, logarithmic above, so 0, 1, 5 ... 35 all get room.
    axes.set_xscale("symlog", linthresh=1, linscale=0.4)
    ticks = [0, *(a.examples_per_label for a in aggregates)]
    axes.set_xticks(ticks, labels=[str(tick) for tick in ticks])
    axes.minorticks_off()
    axes.set_ylim(0, 1)
    axes.yaxis.set_major_formatter(PercentFormatter(xmax=1, decimals=0))
    axes.grid(axis="y", color=_GRIDLINE, linewidth=1, linestyle="-")
    axes.set_axisbelow(True)
    for side in ("top", "right", "left"):
        axes.spines[side].set_visible(False)
    axes.spines["bottom"].set_color(_AXIS)
    axes.tick_params(colors=_INK_MUTED, length=0, labelsize=9)
    axes.set_xlabel("Past examples per category", color=_INK_SECONDARY, fontsize=10)
    axes.set_ylabel("Accuracy", color=_INK_SECONDARY, fontsize=10)


def _plot_examples(axes: Axes, aggregates: Sequence[SeedAggregate]) -> None:
    xs = [a.examples_per_label for a in aggregates]
    axes.fill_between(
        xs,
        [a.min_accuracy for a in aggregates],
        [a.max_accuracy for a in aggregates],
        color=_EXAMPLES_ORANGE,
        alpha=_WASH_ALPHA,
        linewidth=0,
    )
    axes.plot(
        xs,
        [a.mean_accuracy for a in aggregates],
        color=_EXAMPLES_ORANGE,
        linewidth=_LINE_WIDTH,
        marker="o",
        markersize=_MARKER_SIZE,
        markeredgecolor=_SURFACE,
        markeredgewidth=2,
        solid_capstyle="round",
        label="C · cosine vs past examples (mean; band = range over 3 draws)",
    )
    last = aggregates[-1]
    _direct_label(axes, last.examples_per_label, last.mean_accuracy, f"C {last.mean_accuracy:.1%}")


def _plot_descriptions(axes: Axes, description: MethodResult) -> None:
    axes.plot(
        [0],
        [description.accuracy],
        linestyle="none",
        marker="s",
        markersize=_MARKER_SIZE,
        color=_DESCRIPTIONS_AQUA,
        markeredgecolor=_SURFACE,
        markeredgewidth=2,
        label="A · cosine vs descriptions (no examples)",
    )
    _direct_label(axes, 0, description.accuracy, f"A {description.accuracy:.1%}")


def _plot_cross_encoder(axes: Axes, cross_encoder: MethodResult, *, above: float) -> None:
    axes.plot(
        [0],
        [cross_encoder.accuracy],
        linestyle="none",
        marker="D",
        markersize=_MARKER_SIZE - 1,
        color=_CROSS_ENCODER_VIOLET,
        markeredgecolor=_SURFACE,
        markeredgewidth=2,
        label="D · cross-encoder vs descriptions (no examples)",
    )
    # Both A and D sit at x=0: put D's label on the side away from A's so they never collide.
    offset = (8, -14) if cross_encoder.accuracy <= above else (8, 6)
    _direct_label(axes, 0, cross_encoder.accuracy, f"D {cross_encoder.accuracy:.1%}", offset=offset)


def _plot_jev(axes: Axes, jev_result: MethodResult, *, right_edge: int) -> None:
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
        label="B · Jev (no examples; band = 95% CI)",
    )
    _direct_label(axes, right_edge, jev_result.accuracy, f"Jev {jev_result.accuracy:.1%}")


def _direct_label(
    axes: Axes, x: float, y: float, text: str, *, offset: tuple[float, float] = (8, 6)
) -> None:
    axes.annotate(
        text,
        xy=(x, y),
        xytext=offset,
        textcoords="offset points",
        color=_INK_PRIMARY,
        fontsize=9,
    )


def _add_titles(figure: Figure, test_messages: int) -> None:
    figure.suptitle(
        "Do you need Jev, or is cosine similarity enough?",
        x=0.125,
        ha="left",
        color=_INK_PRIMARY,
        fontsize=13,
        fontweight="bold",
    )
    figure.text(
        0.125,
        0.915,
        f"Banking77 intent routing · {test_messages:,} test messages · 77 categories",
        color=_INK_SECONDARY,
        fontsize=9.5,
    )
