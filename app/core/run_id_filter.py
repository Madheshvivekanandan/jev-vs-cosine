"""Logging filter that stamps each record with the current run id."""

import logging

from app.core.run_context import current_run_id


class RunIdFilter(logging.Filter):
    """Adds `run_id` so every line of one invocation can be grepped together."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Attach the run id and keep the record."""
        record.run_id = current_run_id()
        return True
