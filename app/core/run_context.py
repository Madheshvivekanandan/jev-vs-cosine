"""Correlation id for one CLI invocation, attached to every log line."""

import secrets
from contextvars import ContextVar

_run_id: ContextVar[str] = ContextVar("run_id", default="-")


def start_run() -> str:
    """Generate and store a new run id for this invocation."""
    run_id = secrets.token_hex(4)
    _run_id.set(run_id)
    return run_id


def current_run_id() -> str:
    """Return the current run id, or "-" outside a run."""
    return _run_id.get()
