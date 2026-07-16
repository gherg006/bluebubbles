"""Structured logging configuration shared by application entry points."""

import json
import logging
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Final

_STANDARD_RECORD_FIELDS: Final[frozenset[str]] = frozenset(
    logging.makeLogRecord({}).__dict__
)


class JsonFormatter(logging.Formatter):
    """Format log records as machine-readable JSON without mutable global state."""

    def format(self, record: logging.LogRecord) -> str:
        """Return one JSON object for a log record and its safe extra fields."""
        payload: dict[str, object] = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        extras = self._serialisable_extras(record.__dict__)
        if extras:
            payload["context"] = extras
        if record.exc_info is not None:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))

    @staticmethod
    def _serialisable_extras(values: Mapping[str, object]) -> dict[str, object]:
        extras: dict[str, object] = {}
        for key, value in values.items():
            if key in _STANDARD_RECORD_FIELDS or key in {"message", "asctime"}:
                continue
            try:
                json.dumps(value)
            except (TypeError, ValueError):
                extras[key] = repr(value)
            else:
                extras[key] = value
        return extras


def configure_logging(level: str = "INFO") -> logging.Logger:
    """Create and return the isolated root logger for BlueBubbles applications.

    Args:
        level: A standard logging level name such as ``INFO`` or ``DEBUG``.

    Returns:
        The configured ``bluebubbles`` logger.

    Raises:
        ValueError: If ``level`` is not a recognised logging level name.
    """
    normalised_level = level.upper()
    numeric_level = logging.getLevelNamesMapping().get(normalised_level)
    if numeric_level is None:
        raise ValueError(f"Unknown logging level: {level}")

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logger = logging.getLogger("bluebubbles")
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.setLevel(numeric_level)
    logger.propagate = False
    return logger
