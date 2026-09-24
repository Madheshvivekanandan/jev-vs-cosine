"""Provenance printed in REPORT.md, taken from the saved runs rather than live settings."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class ReportContext:
    """What produced the numbers: models, prompt version, route, price, data cleaning.

    `jev_route` and `jev_catalog_version` are None when Jev has not been run, and
    `cross_encoder_model` is None when method D has not been run. `probe_name` is set when
    the results come from a probe set rather than the Banking77 test sample.
    """

    embedding_model: str
    cross_encoder_model: str | None
    catalog_version: str
    train_duplicates_removed: int
    jev_route: str | None
    jev_catalog_version: str | None
    price_usd_per_million_tokens: Decimal
    probe_name: str | None = None
