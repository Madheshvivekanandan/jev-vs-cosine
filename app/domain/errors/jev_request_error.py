"""Error for a Jev request that was rejected or answered unusably."""

from app.domain.errors.app_error import AppError


class JevRequestError(AppError):
    """Jev rejected the request, or returned an answer outside the question's options."""
