"""Formatter that prints structured `extra=` fields as key=value pairs."""

import logging
from typing import Final

from app.utils.printable_text import to_printable

_STANDARD_ATTRIBUTES: Final = frozenset(
    logging.LogRecord("", 0, "", 0, "", None, None).__dict__
) | {"message", "asctime", "run_id", "taskName"}


class KeyValueFormatter(logging.Formatter):
    """Appends every non-standard record attribute, sorted, after the message."""

    def format(self, record: logging.LogRecord) -> str:
        """Return the standard line followed by `key=value` extras."""
        line = super().format(record)
        extras = sorted(
            (key, value)
            for key, value in record.__dict__.items()
            if key not in _STANDARD_ATTRIBUTES
        )
        if not extras:
            return line
        pairs = " ".join(f"{key}={to_printable(str(value))}" for key, value in extras)
        return f"{line} {pairs}"
