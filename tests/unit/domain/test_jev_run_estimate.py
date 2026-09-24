from decimal import Decimal

import pytest

from app.domain.jev_run_estimate import JevRunEstimate


@pytest.mark.parametrize(("estimated", "remaining", "fits"), [(10, 10, True), (11, 10, False)])
def test_fits_budget_compares_estimate_with_remaining(
    estimated: int, remaining: int, *, fits: bool
) -> None:
    estimate = JevRunEstimate(
        cached_messages=0,
        uncached_messages=1,
        estimated_tokens=estimated,
        estimated_list_price_usd=Decimal(0),
        remaining_budget_tokens=remaining,
    )

    assert estimate.fits_budget is fits
