import pytest

from app.domain.errors.budget_exceeded_error import BudgetExceededError
from app.services.token_budget import TokenBudget


def test_ensure_affordable_allows_call_that_exactly_fits() -> None:
    budget = TokenBudget(100, spent_tokens=60)

    budget.ensure_affordable(40)


def test_ensure_affordable_when_over_limit_raises_with_numbers() -> None:
    budget = TokenBudget(100, spent_tokens=60)

    with pytest.raises(BudgetExceededError) as caught:
        budget.ensure_affordable(41)

    assert (caught.value.spent_tokens, caught.value.limit_tokens) == (60, 100)


def test_record_reduces_remaining_and_never_goes_negative() -> None:
    budget = TokenBudget(100)

    budget.record(150)

    assert budget.spent_tokens == 150
    assert budget.remaining_tokens == 0
    assert "150" in repr(budget)


def test_token_budget_with_non_positive_limit_raises() -> None:
    with pytest.raises(ValueError, match="positive"):
        TokenBudget(0)
