"""Logging filter that masks known secret values wherever they appear."""

import logging
from collections.abc import Sequence
from typing import Final

_MASK: Final = "***redacted***"


def mask_secrets(text: str, secret_values: Sequence[str]) -> str:
    """Return `text` with every non-empty secret value replaced by a mask."""
    for secret_value in secret_values:
        if secret_value:
            text = text.replace(secret_value, _MASK)
    return text


class SecretRedactingFilter(logging.Filter):
    """Replaces configured secrets in the message, tracebacks and string extras.

    Masking happens at the logging layer so a careless call site cannot leak the key.
    """

    def __init__(self, secret_values: Sequence[str]) -> None:
        """Remember the values to mask; empty strings are ignored."""
        super().__init__()
        self._secret_values = tuple(value for value in secret_values if value)

    def filter(self, record: logging.LogRecord) -> bool:
        """Redact the record in place and keep it."""
        if not self._secret_values:
            return True
        try:
            message = record.getMessage()
        except (TypeError, ValueError):
            # Malformed %-args: leave the record for the handler's own handleError path.
            return True
        record.msg = self._redact(message)
        record.args = None
        if record.exc_info:
            formatted = logging.Formatter().formatException(record.exc_info)
            record.exc_text = self._redact(formatted)
            record.exc_info = None
        for attribute, value in list(record.__dict__.items()):
            if isinstance(value, str) and attribute != "msg":
                setattr(record, attribute, self._redact(value))
        return True

    def _redact(self, text: str) -> str:
        return mask_secrets(text, self._secret_values)
