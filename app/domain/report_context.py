"""Provenance printed in REPORT.md, taken from the saved runs rather than live settings."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class ReportContext:
    """What produced the numbers: models, prompt version, route, price, data cleaning.

    `jev_route` and `jev_catalog_version` are None when Jev has not been run.
    """

    embedding_model: str
    catalog_version: str
    train_duplicates_removed: int
    jev_route: str | None
    jev_catalog_version: str | None
    price_usd_per_million_tokens: Decimal
