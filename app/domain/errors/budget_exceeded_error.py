"""Error raised before a Jev call that would break the token budget."""

from app.domain.errors.app_error import AppError


class BudgetExceededError(AppError):
    """The next Jev call would push total input tokens past the configured ceiling."""

    def __init__(self, spent_tokens: int, estimated_tokens: int, limit_tokens: int) -> None:
        """Record how close the run came to the ceiling.

        Args:
            spent_tokens: Input tokens already used, including cached earlier runs.
            estimated_tokens: Estimated input tokens of the call that was refused.
            limit_tokens: The configured ceiling.
        """
        super().__init__(
            f"next call (~{estimated_tokens} tokens) would exceed the budget: "
            f"{spent_tokens} of {limit_tokens} input tokens already used"
        )
        self.spent_tokens = spent_tokens
        self.estimated_tokens = estimated_tokens
        self.limit_tokens = limit_tokens
