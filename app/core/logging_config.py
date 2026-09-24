"""Configure logging once, at CLI start-up."""

import logging
import sys
from collections.abc import Sequence
from typing import Final

from app.core.key_value_formatter import KeyValueFormatter
from app.core.run_id_filter import RunIdFilter
from app.core.secret_redacting_filter import SecretRedactingFilter

_FORMAT: Final = "%(asctime)s %(levelname)s %(name)s run=%(run_id)s %(message)s"


def configure_logging(level: str, *, secret_values: Sequence[str]) -> None:
    """Send logs to stderr with run ids, key=value extras and secret masking.

    The TypeSafe SDK logs full request and response bodies at DEBUG, so its logger is
    held at WARNING: message content stays out of logs by default.
    """
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(KeyValueFormatter(_FORMAT))
    handler.addFilter(RunIdFilter())
    handler.addFilter(SecretRedactingFilter(secret_values))
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level)
    logging.getLogger("typesafe_sdk").setLevel(logging.WARNING)
    # httpx2 (TypeSafe SDK) and httpx (Hugging Face downloads) log one INFO line per request.
    for http_logger in ("httpx2", "httpx"):
        logging.getLogger(http_logger).setLevel(logging.WARNING)
