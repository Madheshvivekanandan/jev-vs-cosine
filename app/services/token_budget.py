"""Hard ceiling on Jev input tokens across all runs of the experiment."""

from app.domain.errors.budget_exceeded_error import BudgetExceededError


class TokenBudget:
    """Refuses any call that would push total input tokens past the limit.

    This is a stop, not an alert: free credit is finite, and a runaway loop spends it
    faster than anyone can react to a warning.
    """

    def __init__(self, limit_tokens: int, *, spent_tokens: int = 0) -> None:
        """Start the budget, counting tokens already spent by earlier runs.

        Args:
            limit_tokens: Maximum total input tokens for the whole experiment.
            spent_tokens: Tokens already used (from the response cache).
        """
        if limit_tokens <= 0:
            raise ValueError("limit_tokens must be positive")
        self._limit_tokens = limit_tokens
        self._spent_tokens = spent_tokens

    def __repr__(self) -> str:
        """Show usage for debugging."""
        return f"TokenBudget(spent={self._spent_tokens}, limit={self._limit_tokens})"

    @property
    def spent_tokens(self) -> int:
        """Return input tokens used so far."""
        return self._spent_tokens

    @property
    def remaining_tokens(self) -> int:
        """Return input tokens left before the ceiling."""
        return max(0, self._limit_tokens - self._spent_tokens)

    def ensure_affordable(self, estimated_tokens: int) -> None:
        """Raise before a call that would exceed the ceiling.

        Raises:
            BudgetExceededError: If `estimated_tokens` does not fit in what remains.
        """
        if self._spent_tokens + estimated_tokens > self._limit_tokens:
            raise BudgetExceededError(self._spent_tokens, estimated_tokens, self._limit_tokens)

    def record(self, tokens: int) -> None:
        """Add the tokens a completed call actually used."""
        self._spent_tokens += tokens
