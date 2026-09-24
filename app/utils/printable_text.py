"""Make untrusted text safe to print on one terminal or log line."""

from typing import Final

_DEFAULT_MAX_LENGTH: Final = 500


def to_printable(text: str, *, max_length: int = _DEFAULT_MAX_LENGTH) -> str:
    """Return `text` with control characters escaped and length capped.

    Provider error messages end up in logs and on stderr; an embedded newline or ANSI
    escape could otherwise forge or hide log lines.
    """
    safe = text if text.isprintable() else text.encode("unicode_escape").decode("ascii")
    if len(safe) <= max_length:
        return safe
    return safe[:max_length] + "…"
