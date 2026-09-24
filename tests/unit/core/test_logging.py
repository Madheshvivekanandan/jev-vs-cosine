import logging

import pytest

from app.core.key_value_formatter import KeyValueFormatter
from app.core.logging_config import configure_logging
from app.core.run_context import current_run_id, start_run
from app.core.run_id_filter import RunIdFilter
from app.core.secret_redacting_filter import SecretRedactingFilter


def _record(message: str, *args: object, **extra: object) -> logging.LogRecord:
    record = logging.LogRecord("test", logging.INFO, __file__, 1, message, args, None)
    for key, value in extra.items():
        setattr(record, key, value)
    return record


def test_secret_redacting_filter_masks_message_args_and_extras() -> None:
    record = _record("key is %s", "sk-123", header="Bearer sk-123")

    SecretRedactingFilter(["sk-123"]).filter(record)

    assert "sk-123" not in record.getMessage()
    assert record.header == "Bearer ***redacted***"


def test_secret_redacting_filter_without_secrets_leaves_record_alone() -> None:
    record = _record("hello %s", "world")

    SecretRedactingFilter([""]).filter(record)

    assert record.getMessage() == "hello world"


def test_run_id_filter_stamps_the_current_run() -> None:
    run_id = start_run()
    record = _record("x")

    RunIdFilter().filter(record)

    assert record.run_id == run_id == current_run_id()


def test_key_value_formatter_appends_sorted_extras() -> None:
    record = _record("jev_call", tokens=10, model="m")
    record.run_id = "r"

    line = KeyValueFormatter("%(message)s").format(record)

    assert line == "jev_call model=m tokens=10"


def test_configure_logging_silences_sdk_body_logging(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging("INFO", secret_values=["sk-xyz"])

    logging.getLogger("typesafe_sdk").info("request body with sk-xyz")
    logging.getLogger("app.test").info("hello sk-xyz")

    captured = capsys.readouterr().err
    assert "request body" not in captured
    assert "hello ***redacted***" in captured


def test_secret_redacting_filter_masks_secrets_in_tracebacks() -> None:
    try:
        raise RuntimeError("upstream said sk-123 is invalid")
    except RuntimeError:
        import sys  # noqa: PLC0415 - only this test needs exc_info

        record = logging.LogRecord("t", logging.ERROR, __file__, 1, "failed", None, sys.exc_info())

    SecretRedactingFilter(["sk-123"]).filter(record)

    assert record.exc_info is None
    assert record.exc_text is not None
    assert "sk-123" not in record.exc_text
    assert "***redacted***" in record.exc_text


def test_secret_redacting_filter_leaves_malformed_records_for_the_handler() -> None:
    record = _record("two args %s %s", "only-one")

    assert SecretRedactingFilter(["sk-123"]).filter(record) is True
    assert record.args == ("only-one",)


def test_key_value_formatter_escapes_control_characters() -> None:
    record = _record("command_failed", reason="line one\nFAKE INFO line\x1b[31m")
    record.run_id = "r"

    line = KeyValueFormatter("%(message)s").format(record)

    assert "\n" not in line
    assert "\x1b" not in line
    assert "\\n" in line
