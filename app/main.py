"""Command-line entry point: download, run-cosine, run-jev, report.

Usage: python -m app.main <command> [options]
"""

import argparse
import dataclasses
import logging
import sys
import time
from collections.abc import Callable, Mapping, Sequence
from decimal import Decimal
from typing import Final

from pydantic import ValidationError

from app.clients.cross_encoder_scorer import load_cross_encoder_scorer
from app.clients.logistic_regression_trainer import LogisticRegressionTrainer
from app.clients.sentence_transformer_embedder import load_sentence_transformer_embedder
from app.clients.typesafe_jev_decider import TypeSafeJevDecider, create_typesafe_client
from app.core.jev_route import JevRoute
from app.core.logging_config import configure_logging
from app.core.run_context import start_run
from app.core.secret_redacting_filter import mask_secrets
from app.core.settings import BenchmarkSettings
from app.domain.benchmark_inputs import BenchmarkInputs
from app.domain.benchmark_method import BenchmarkMethod
from app.domain.benchmark_results import BenchmarkResults
from app.domain.dataset_split import DatasetSplit
from app.domain.errors.app_error import AppError
from app.domain.errors.configuration_error import ConfigurationError
from app.domain.experiment_design import ExperimentDesign
from app.domain.intent_catalog import IntentCatalog
from app.domain.labeled_message import LabeledMessage
from app.domain.method_run import MethodRun
from app.domain.metrics import summarize
from app.domain.prediction import Prediction
from app.domain.report_context import ReportContext
from app.repositories.banking77_repository import Banking77Repository, fetch_https
from app.repositories.intent_catalog_repository import load_intent_catalog
from app.repositories.jev_decision_cache_repository import JevDecisionCacheRepository
from app.repositories.results_repository import ResultsRepository
from app.services.call_pacer import CallPacer
from app.services.chart_service import CHART_FILENAME, render_accuracy_chart
from app.services.cosine_benchmark_service import CosineBenchmarkService
from app.services.cross_encoder_benchmark_service import CrossEncoderBenchmarkService
from app.services.dataset_checks import ensure_catalog_matches_dataset, remove_test_duplicates
from app.services.jev_benchmark_service import JevBenchmarkService
from app.services.report_builder import build_markdown_report
from app.services.sampling import sample_test_set
from app.services.token_budget import TokenBudget
from app.services.trained_classifier_benchmark_service import TrainedClassifierBenchmarkService
from app.utils.printable_text import to_printable

logger = logging.getLogger(__name__)

_DESIGN: Final = ExperimentDesign()
_EXIT_OK: Final = 0
_EXIT_APP_ERROR: Final = 1
_EXIT_CRASH: Final = 2

type Command = Callable[[BenchmarkSettings, argparse.Namespace], int]


def build_parser() -> argparse.ArgumentParser:
    """Return the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="jev-vs-cosine",
        description="Benchmark TypeSafe Jev against cosine similarity on Banking77.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("download", help="download and verify the Banking77 dataset")
    cosine = commands.add_parser("run-cosine", help="run methods A and C locally (free, no key)")
    jev = commands.add_parser("run-jev", help="run method B (Jev) with cache and budget")
    jev.add_argument("--dry-run", action="store_true", help="estimate tokens; call nothing")
    cross = commands.add_parser(
        "run-cross-encoder", help="run method D (cross-encoder) locally (free, no key)"
    )
    trained = commands.add_parser(
        "run-trained", help="run method E (classifier trained on past examples) locally"
    )
    report = commands.add_parser("report", help="write REPORT.md and the chart")
    for command in (cosine, jev, cross, trained, report):
        command.add_argument(
            "--limit",
            type=int,
            default=None,
            help="only the first N messages of the shuffled test sample; results go to "
            "results/first_N/ so every method is scored on the same messages",
        )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run one CLI command and return its exit code."""
    arguments = build_parser().parse_args(argv)
    try:
        settings = _load_settings()
    except ConfigurationError as exc:
        print(f"error: {to_printable(str(exc))}", file=sys.stderr)
        return _EXIT_APP_ERROR
    secret = settings.jev_api_key.get_secret_value() if settings.jev_api_key else ""
    configure_logging(settings.log_level, secret_values=[secret])
    start_run()
    try:
        return _COMMANDS[arguments.command](settings, arguments)
    except AppError as exc:
        reason = to_printable(mask_secrets(str(exc), [secret]))
        logger.error("command_failed", extra={"command": arguments.command, "reason": reason})
        print(f"error: {reason}", file=sys.stderr)
        return _EXIT_APP_ERROR
    except Exception:
        logger.exception("command_crashed", extra={"command": arguments.command})
        return _EXIT_CRASH


def _load_settings() -> BenchmarkSettings:
    try:
        return BenchmarkSettings()
    except ValidationError as exc:
        # Location and message only: never the offending value, which may be a key.
        problems = "; ".join(
            f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}"
            for error in exc.errors(include_input=False, include_url=False)
        )
        raise ConfigurationError(f"invalid settings ({problems}); see .env.example") from exc


def _download(settings: BenchmarkSettings, _arguments: argparse.Namespace) -> int:
    Banking77Repository(settings.data_dir, fetch_https).ensure_downloaded()
    print(f"Banking77 downloaded and verified under {settings.data_dir}/banking77/")
    return _EXIT_OK


def _load_inputs(settings: BenchmarkSettings) -> BenchmarkInputs:
    repository = Banking77Repository(settings.data_dir, fetch_https)
    repository.ensure_downloaded()
    full_train_set = repository.load(DatasetSplit.TRAIN)
    full_test_set = repository.load(DatasetSplit.TEST)
    catalog = load_intent_catalog(settings.catalog_path)
    ensure_catalog_matches_dataset(catalog, full_train_set)
    ensure_catalog_matches_dataset(catalog, full_test_set)
    train_set, removed = remove_test_duplicates(full_train_set, full_test_set)
    logger.info("train_test_duplicates_removed", extra={"count": removed})
    test_set = sample_test_set(
        full_test_set,
        per_label=_DESIGN.test_messages_per_label,
        seed=_DESIGN.test_sample_seed,
    )
    return BenchmarkInputs(catalog, test_set, train_set, removed)


def _run_cosine(settings: BenchmarkSettings, arguments: argparse.Namespace) -> int:
    inputs = _load_inputs(settings)
    test_set = _apply_limit(inputs.test_set, arguments.limit)
    embedder = load_sentence_transformer_embedder(
        settings.embedding_model_name, settings.embedding_model_revision
    )
    service = CosineBenchmarkService(embedder, _DESIGN, clock=time.perf_counter)
    runs = service.run(inputs.catalog, test_set, inputs.train_set)
    results = _results_for(settings, arguments.limit)
    path = results.save_runs("cosine", runs)
    results.save_metadata(
        "cosine",
        {
            "catalog_version": inputs.catalog.version,
            "catalog_fingerprint": inputs.catalog.fingerprint(),
            "embedding_model": f"{settings.embedding_model_name}@{settings.embedding_model_revision}",
            "train_duplicates_removed": str(inputs.train_duplicates_removed),
        },
    )
    _print_cosine_summary(runs)
    print(f"saved {path}")
    return _EXIT_OK


def _print_cosine_summary(runs: Sequence[MethodRun]) -> None:
    # Also used by run-trained: one line per (method, examples per label, seed).
    for run in runs:
        result = run.result
        seed = f" seed {result.seed}" if result.seed is not None else ""
        print(
            f"{result.method.value:<22} examples/label={result.examples_per_label:<3}{seed:<8} "
            f"accuracy={result.accuracy:.1%}"
        )


def _run_cross_encoder(settings: BenchmarkSettings, arguments: argparse.Namespace) -> int:
    inputs = _load_inputs(settings)
    test_set = _apply_limit(inputs.test_set, arguments.limit)
    scorer = load_cross_encoder_scorer(
        settings.cross_encoder_model_name, settings.cross_encoder_model_revision
    )
    run = CrossEncoderBenchmarkService(scorer, clock=time.perf_counter).run(
        inputs.catalog, test_set
    )
    results = _results_for(settings, arguments.limit)
    path = results.save_runs("cross_encoder", [run])
    model = f"{settings.cross_encoder_model_name}@{settings.cross_encoder_model_revision}"
    results.save_metadata(
        "cross_encoder",
        {
            "cross_encoder_model": model,
            "catalog_version": inputs.catalog.version,
            "catalog_fingerprint": inputs.catalog.fingerprint(),
        },
    )
    print(
        f"{run.result.method.value} accuracy={run.result.accuracy:.1%}; "
        f"median {run.result.median_latency_ms:.0f} ms per message"
    )
    print(f"saved {path}")
    return _EXIT_OK


def _run_trained(settings: BenchmarkSettings, arguments: argparse.Namespace) -> int:
    inputs = _load_inputs(settings)
    test_set = _apply_limit(inputs.test_set, arguments.limit)
    embedder = load_sentence_transformer_embedder(
        settings.embedding_model_name, settings.embedding_model_revision
    )
    service = TrainedClassifierBenchmarkService(
        embedder, LogisticRegressionTrainer(), _DESIGN, clock=time.perf_counter
    )
    runs = service.run(test_set, inputs.train_set)
    results = _results_for(settings, arguments.limit)
    path = results.save_runs("trained_classifier", runs)
    results.save_metadata(
        "trained_classifier",
        {
            "classifier": "scikit-learn LogisticRegression(C=100, max_iter=5000)",
            "embedding_model": f"{settings.embedding_model_name}@{settings.embedding_model_revision}",
            "train_duplicates_removed": str(inputs.train_duplicates_removed),
        },
    )
    _print_cosine_summary(runs)
    print(f"saved {path}")
    return _EXIT_OK


def _run_jev(settings: BenchmarkSettings, arguments: argparse.Namespace) -> int:
    route = settings.require_jev_route()
    inputs = _load_inputs(settings)
    test_set = _apply_limit(inputs.test_set, arguments.limit)
    cache = JevDecisionCacheRepository(settings.cache_dir / "jev_decisions.jsonl")
    budget = TokenBudget(
        settings.jev_max_total_input_tokens, spent_tokens=cache.total_input_tokens()
    )
    pacer = CallPacer(
        settings.jev_min_seconds_between_calls, clock=time.monotonic, sleep=time.sleep
    )
    with create_typesafe_client(
        api_key=route.api_key,
        base_url=route.base_url,
        timeout_seconds=settings.jev_timeout_seconds,
        max_retries=settings.jev_max_retries,
    ) as client:
        decider = TypeSafeJevDecider(client, model=route.model)
        service = JevBenchmarkService(decider, cache, budget, pacer)
        if arguments.dry_run:
            return _print_estimate(service, inputs.catalog, test_set, settings, route.route_id)
        predictions = service.run(inputs.catalog, test_set, route_id=route.route_id)
        served = service.served_models(inputs.catalog, test_set, route_id=route.route_id)
    results = _results_for(settings, arguments.limit)
    _save_jev_result(settings, predictions, budget, results)
    results.save_metadata("jev", _jev_metadata(route, served, inputs.catalog, settings))
    return _EXIT_OK


def _jev_metadata(
    route: JevRoute,
    served_models: Sequence[str],
    catalog: IntentCatalog,
    settings: BenchmarkSettings,
) -> dict[str, str]:
    return {
        "route_id": route.route_id,
        "served_models": ", ".join(served_models),
        "catalog_version": catalog.version,
        "catalog_fingerprint": catalog.fingerprint(),
        "price_usd_per_million_input_tokens": str(settings.jev_price_usd_per_million_input_tokens),
    }


def _apply_limit(test_set: list[LabeledMessage], limit: int | None) -> list[LabeledMessage]:
    if limit is None:
        return test_set
    if limit < 1:
        raise ConfigurationError("--limit must be at least 1")
    return test_set[:limit]


def _results_for(settings: BenchmarkSettings, limit: int | None) -> ResultsRepository:
    # A limited run is a different experiment: keep it apart from the full-sample results.
    if limit is None:
        return ResultsRepository(settings.results_dir)
    return ResultsRepository(settings.results_dir / f"first_{limit}")


def _save_jev_result(
    settings: BenchmarkSettings,
    predictions: Sequence[Prediction],
    budget: TokenBudget,
    results: ResultsRepository,
) -> None:
    result = summarize(
        BenchmarkMethod.JEV,
        predictions,
        examples_per_label=0,
        seed=None,
        price_usd_per_million_tokens=settings.jev_price_usd_per_million_input_tokens,
    )
    results.save_runs("jev", [MethodRun(result, tuple(predictions))])
    print(
        f"Jev accuracy={result.accuracy:.1%} on {result.total} messages; "
        f"input tokens this result={result.input_tokens:,}; "
        f"total spent={budget.spent_tokens:,} of {settings.jev_max_total_input_tokens:,}"
    )


def _print_estimate(
    service: JevBenchmarkService,
    catalog: IntentCatalog,
    test_set: Sequence[LabeledMessage],
    settings: BenchmarkSettings,
    route_id: str,
) -> int:
    estimate = service.estimate(
        catalog,
        test_set,
        route_id=route_id,
        price_usd_per_million_tokens=settings.jev_price_usd_per_million_input_tokens,
    )
    print(
        f"dry run: {estimate.uncached_messages} calls needed ({estimate.cached_messages} cached), "
        f"~{estimate.estimated_tokens:,} input tokens, "
        f"~${estimate.estimated_list_price_usd:.4f} at list price; "
        f"budget remaining {estimate.remaining_budget_tokens:,} tokens; "
        f"fits={'yes' if estimate.fits_budget else 'NO'}"
    )
    return _EXIT_OK


def _report(settings: BenchmarkSettings, arguments: argparse.Namespace) -> int:
    results = _results_for(settings, arguments.limit)
    cosine_results = results.load_results("cosine")
    if not cosine_results:
        raise ConfigurationError("no cosine results yet; run `run-cosine` first")
    jev_results = results.load_results("jev")
    jev_result = jev_results[0] if jev_results else None
    jev_metadata = results.load_metadata("jev") if jev_result is not None else {}
    cross_results = results.load_results("cross_encoder")
    cross_result = cross_results[0] if cross_results else None
    context = _report_context(results.load_metadata("cosine"), jev_metadata, settings)
    if cross_result is not None:
        cross_model = results.load_metadata("cross_encoder").get("cross_encoder_model")
        context = dataclasses.replace(context, cross_encoder_model=cross_model or "unknown")
    bundle = BenchmarkResults(
        cosine=cosine_results,
        jev=jev_result,
        cross_encoder=cross_result,
        trained=results.load_results("trained_classifier"),
    )
    render_accuracy_chart(bundle, results.path_for(CHART_FILENAME))
    report = build_markdown_report(bundle, context)
    print(f"wrote {results.write_text('REPORT.md', report)}")
    return _EXIT_OK


def _report_context(
    cosine_metadata: Mapping[str, str],
    jev_metadata: Mapping[str, str],
    settings: BenchmarkSettings,
) -> ReportContext:
    # Provenance comes from what each run saved, never from the current .env.
    jev_route = None
    if jev_metadata:
        served = jev_metadata.get("served_models") or "unknown"
        jev_route = f"`{jev_metadata.get('route_id', 'unknown')}` (model reported: {served})"
    default_price = str(settings.jev_price_usd_per_million_input_tokens)
    return ReportContext(
        embedding_model=cosine_metadata.get("embedding_model", "unknown"),
        cross_encoder_model=None,
        catalog_version=cosine_metadata.get("catalog_version", "unknown"),
        train_duplicates_removed=int(cosine_metadata.get("train_duplicates_removed", "0")),
        jev_route=jev_route,
        jev_catalog_version=jev_metadata.get("catalog_version"),
        price_usd_per_million_tokens=Decimal(
            jev_metadata.get("price_usd_per_million_input_tokens", default_price)
        ),
    )


_COMMANDS: Final[dict[str, Command]] = {
    "download": _download,
    "run-cosine": _run_cosine,
    "run-jev": _run_jev,
    "run-cross-encoder": _run_cross_encoder,
    "run-trained": _run_trained,
    "report": _report,
}


if __name__ == "__main__":
    sys.exit(main())
