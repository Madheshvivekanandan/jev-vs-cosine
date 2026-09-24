"""Error for a dataset that cannot support the experiment design."""

from app.domain.errors.app_error import AppError


class DatasetError(AppError):
    """The dataset file is malformed, fails its checksum, or has too few examples."""
