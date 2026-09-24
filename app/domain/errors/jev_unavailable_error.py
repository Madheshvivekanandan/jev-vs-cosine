"""Error for a transient Jev failure that outlasted the SDK's retries."""

from app.domain.errors.app_error import AppError


class JevUnavailableError(AppError):
    """Jev was rate-limited, overloaded or unreachable; re-running later resumes from the cache."""
