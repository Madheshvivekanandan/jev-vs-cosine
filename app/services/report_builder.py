"""Build the Markdown results table from saved method results."""

from collections.abc import Sequence

from app.domain.benchmark_method import BenchmarkMethod
from app.domain.benchmark_results import BenchmarkResults
from app.domain.method_result import MethodResult
from app.domain.report_context import ReportContext
from app.domain.seed_aggregate import SeedAggregate, aggregate_across_seeds
from app.services.chart_service import CHART_FILENAME

_HEADER = (
    "| Method | Past examples per category | Accuracy (95% CI) | Median latency | "
    "p95 latency | Input tokens | List-price cost |\n"
    "|---|---|---|---|---|---|---|"
)


_C_NAME = "C · cosine vs past examples (top-5 vote)"
_E_NAME = "E · classifier trained on past examples"


def build_markdown_report(results: BenchmarkResults, context: ReportContext) -> str:
    """Return the full REPORT.md text: headline, chart, table and how to read it."""
    description = _only(results.cosine, BenchmarkMethod.COSINE_DESCRIPTIONS)
    examples = [r for r in results.cosine if r.method is BenchmarkMethod.COSINE_EXAMPLES]
    aggregates = aggregate_across_seeds(examples)
    sections = [
        "# Results: Jev vs cosine similarity on Banking77",
        "\n\n".join(_headlines(results, description, aggregates)),
        f"![Accuracy vs past examples per category]({CHART_FILENAME})",
        "\n".join([_HEADER, *_rows(results, description, examples)]),
        _notes(description.total, aggregates, context),
    ]
    return "\n\n".join(sections) + "\n"


def _rows(
    results: BenchmarkResults, description: MethodResult, examples: Sequence[MethodResult]
) -> list[str]:
    rows = [_result_row("A · cosine vs descriptions", description)]
    if results.jev is not None:
        rows.append(_result_row("B · Jev", results.jev))
    if results.cross_encoder is not None:
        rows.append(_result_row("D · cross-encoder vs descriptions", results.cross_encoder))
    rows.extend(_aggregate_row(_C_NAME, a, examples) for a in aggregate_across_seeds(examples))
    trained = list(results.trained)
    rows.extend(_aggregate_row(_E_NAME, a, trained) for a in aggregate_across_seeds(trained))
    return rows


def _headlines(
    results: BenchmarkResults, description: MethodResult, aggregates: Sequence[SeedAggregate]
) -> list[str]:
    lines = [_headline(description, results.jev, aggregates)]
    if results.trained:
        lines.append(_trained_line(results.jev, aggregate_across_seeds(results.trained)))
    if results.cross_encoder is not None:
        lines.append(_cross_encoder_line(description, results.jev, results.cross_encoder))
    return lines


def _trained_line(jev_result: MethodResult | None, trained: Sequence[SeedAggregate]) -> str:
    best = trained[-1]
    if jev_result is None:
        return (
            f"A classifier trained on the same past examples (method E) reaches "
            f"**{best.mean_accuracy:.1%}** with {best.examples_per_label} per category."
        )
    crossover = find_crossover(trained, jev_result.accuracy)
    reach = (
        f"reaches Jev at **{crossover} examples per category**"
        if crossover is not None
        else "does not reach Jev within the tested range"
    )
    return (
        f"A classifier trained on the same past examples (method E) {reach}, and scores "
        f"{best.mean_accuracy:.1%} with {best.examples_per_label} per category."
    )


def _cross_encoder_line(
    description: MethodResult, jev_result: MethodResult | None, cross_encoder: MethodResult
) -> str:
    baseline = jev_result if jev_result is not None else description
    name = "Jev" if jev_result is not None else "cosine vs descriptions"
    gap_points = (cross_encoder.accuracy - baseline.accuracy) * 100
    return (
        f"A local cross-encoder that reads each message together with each description "
        f"(method D) scores **{cross_encoder.accuracy:.1%}**, {gap_points:+.1f} points vs {name}, "
        f"at {cross_encoder.median_latency_ms:.0f} ms per message on CPU."
    )


def find_crossover(aggregates: Sequence[SeedAggregate], jev_accuracy: float) -> int | None:
    """Return the first tested examples-per-category whose mean accuracy reaches Jev."""
    return next((a.examples_per_label for a in aggregates if a.mean_accuracy >= jev_accuracy), None)


def _headline(
    description: MethodResult,
    jev_result: MethodResult | None,
    aggregates: Sequence[SeedAggregate],
) -> str:
    if jev_result is None:
        return "_Jev (method B) has not been run yet; only the cosine methods are shown._"
    if jev_result.accuracy <= description.accuracy:
        return (
            f"**With no examples, cosine vs descriptions already matches or beats Jev "
            f"({description.accuracy:.1%} vs {jev_result.accuracy:.1%}).**"
        )
    gap_points = (jev_result.accuracy - description.accuracy) * 100
    crossover = find_crossover(aggregates, jev_result.accuracy)
    catch_up = (
        f"the first tested setting where cosine vs past examples reaches Jev is "
        f"{crossover} examples per category."
        if crossover is not None
        else "cosine vs past examples does not reach Jev within the tested range."
    )
    return f"**With no examples, Jev leads cosine by {gap_points:.1f} points; {catch_up}**"


def _result_row(name: str, result: MethodResult) -> str:
    return (
        f"| {name} | {result.examples_per_label} | {_accuracy_with_ci(result)} | "
        f"{result.median_latency_ms:.0f} ms | {result.p95_latency_ms:.0f} ms | "
        f"{result.input_tokens:,} | ${result.list_price_cost_usd:.4f} |"
    )


def _aggregate_row(name: str, aggregate: SeedAggregate, examples: Sequence[MethodResult]) -> str:
    same_setting = [r for r in examples if r.examples_per_label == aggregate.examples_per_label]
    median_ms = sum(r.median_latency_ms for r in same_setting) / len(same_setting)
    p95_ms = sum(r.p95_latency_ms for r in same_setting) / len(same_setting)
    accuracy = (
        f"{aggregate.mean_accuracy:.1%} (range {aggregate.min_accuracy:.1%}–"
        f"{aggregate.max_accuracy:.1%} over {aggregate.run_count} draws)"
    )
    return (
        f"| {name} | {aggregate.examples_per_label} | "
        f"{accuracy} | {median_ms:.0f} ms | {p95_ms:.0f} ms | 0 | $0.0000 |"
    )


def _accuracy_with_ci(result: MethodResult) -> str:
    return f"{result.accuracy:.1%} ({result.accuracy_ci_low:.1%}–{result.accuracy_ci_high:.1%})"


def _notes(test_messages: int, aggregates: Sequence[SeedAggregate], context: ReportContext) -> str:
    grid = ", ".join(str(a.examples_per_label) for a in aggregates)
    lines = [
        "## How to read this",
        "",
        f"- Every method answered the same {test_messages:,} test messages from the Banking77 "
        "test split. The full sample is 13 per category x 77 categories = 1,001, shuffled; "
        "a smaller count means the first N of that sample.",
        "- A embeds each category's name plus its one-line description. B (Jev) gets the same "
        "names and descriptions as Choice options, plus a one-sentence instruction. C compares "
        f"against past customer messages from the training split ({grid} per category), "
        f"drawn with 3 random seeds; {context.train_duplicates_removed} training rows that "
        "duplicated a test message (ignoring case and whitespace) were removed first.",
        f"- Prompt catalog: `{context.catalog_version}`. Embedding model: "
        f"`{context.embedding_model}`, run locally on CPU (free). "
        f"Jev: {context.jev_route or 'not run'}.",
        "- D scores (message, name + description) for every category with a cross-encoder "
        f"reranker (`{context.cross_encoder_model or 'not run'}`), 77 pairs per message, locally "
        "on CPU, with no examples. Its latency is all 77 pairs for one message.",
        "- E trains a logistic-regression classifier on the embeddings of the same past "
        "examples C votes with (same seeds, same messages). Training is offline and untimed.",
        "- Latency for A and C is local embedding plus scoring per message. For Jev it is the "
        "full network round trip, including retry waits on routes with retries enabled.",
        "- List-price cost is what the run would cost at "
        f"${context.price_usd_per_million_tokens} per million input tokens, even when the "
        "route used was free.",
    ]
    if context.jev_catalog_version not in (None, context.catalog_version):
        lines.append(
            f"- **Warning:** Jev ran with catalog `{context.jev_catalog_version}`, the cosine "
            f"methods with `{context.catalog_version}`; the comparison is not like for like."
        )
    return "\n".join(lines)


def _only(results: Sequence[MethodResult], method: BenchmarkMethod) -> MethodResult:
    matches = [result for result in results if result.method is method]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one {method} result, found {len(matches)}")
    return matches[0]
