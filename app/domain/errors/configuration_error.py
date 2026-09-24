"""Error for missing or inconsistent configuration."""

from app.domain.errors.app_error import AppError


class ConfigurationError(AppError):
    """Settings, credentials or the prompt catalog are missing or do not match the dataset."""
