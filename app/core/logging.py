"""
Structured JSON logging configuration.
"""

import logging
import sys
from typing import Any


class JSONFormatter(logging.Formatter):
    """Outputs structured log lines as JSON for production log aggregators."""

    def format(self, record: logging.LogRecord) -> str:
        import json
        log_entry: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id  # type: ignore[attr-defined]
        return json.dumps(log_entry)


def setup_logging(level: str = "INFO", json_output: bool = False) -> None:
    """
    Configures the root logger.
    - json_output=True  → machine-readable JSON lines (production)
    - json_output=False → human-readable format (development)
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    if json_output:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
    root_logger.addHandler(handler)

    # Quiet noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("prisma").setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """Returns a named logger for use in modules."""
    return logging.getLogger(name)
