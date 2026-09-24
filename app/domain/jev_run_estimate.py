"""What a Jev run would do, computed without calling Jev."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class JevRunEstimate:
    """Pre-flight numbers for a dry run: how many calls, tokens and dollars remain."""

    cached_messages: int
    uncached_messages: int
    estimated_tokens: int
    estimated_list_price_usd: Decimal
    remaining_budget_tokens: int

    @property
    def fits_budget(self) -> bool:
        """Return whether the estimated tokens fit in the remaining budget."""
        return self.estimated_tokens <= self.remaining_budget_tokens
