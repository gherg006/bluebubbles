"""Tests for structured application logging."""

import json
import logging
import sys

import pytest

from bluebubbles.shared.logging import JsonFormatter, configure_logging


def test_json_formatter_includes_context() -> None:
    record = logging.LogRecord(
        name="bluebubbles.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="Server started",
        args=(),
        exc_info=None,
    )
    record.correlation_id = "test-correlation"

    payload = json.loads(JsonFormatter().format(record))

    assert payload["message"] == "Server started"
    assert payload["context"] == {"correlation_id": "test-correlation"}


def test_json_formatter_represents_non_serialisable_context() -> None:
    record = logging.makeLogRecord({"msg": "event", "context_value": object()})

    payload = json.loads(JsonFormatter().format(record))

    assert isinstance(payload["context"]["context_value"], str)


def test_configure_logging_rejects_unknown_level() -> None:
    with pytest.raises(ValueError, match="Unknown logging level"):
        configure_logging("not-a-level")


def test_configure_logging_replaces_existing_handlers() -> None:
    logger = logging.getLogger("bluebubbles")
    logger.addHandler(logging.NullHandler())

    configured = configure_logging("debug")

    assert configured.level == logging.DEBUG
    assert len(configured.handlers) == 1
    assert isinstance(configured.handlers[0].formatter, JsonFormatter)
    assert configured.propagate is False


def test_json_formatter_includes_exception_details() -> None:
    try:
        raise RuntimeError("safe test failure")
    except RuntimeError:
        exception_info = sys.exc_info()

    record = logging.LogRecord(
        name="bluebubbles.test",
        level=logging.ERROR,
        pathname=__file__,
        lineno=1,
        msg="Operation failed",
        args=(),
        exc_info=exception_info,
    )

    payload = json.loads(JsonFormatter().format(record))

    assert "RuntimeError: safe test failure" in payload["exception"]
