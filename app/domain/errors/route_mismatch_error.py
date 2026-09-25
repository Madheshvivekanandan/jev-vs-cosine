"""Error for a Jev route whose answers no longer match TypeSafe's published ones."""

from app.domain.errors.app_error import AppError


class RouteMismatchError(AppError):
    """Replayed reference cases did not match: the route may serve a different model."""
