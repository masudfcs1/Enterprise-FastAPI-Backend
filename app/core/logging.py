"""
Structured and colored logging configuration.
Provides rich ANSI terminal formatting for development and JSON for production.
"""

import logging
import sys
from typing import Any

try:
    import colorama

    colorama.init(autoreset=True)
except ImportError:
    pass

# ── ANSI Color Tokens ─────────────────────────────────────
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

# Foreground Colors
FG_RED = "\033[31m"
FG_GREEN = "\033[32m"
FG_YELLOW = "\033[33m"
FG_BLUE = "\033[34m"
FG_MAGENTA = "\033[35m"
FG_CYAN = "\033[36m"
FG_WHITE = "\033[37m"
FG_GRAY = "\033[90m"

# Bold Foreground Colors
BOLD_RED = "\033[1;31m"
BOLD_GREEN = "\033[1;32m"
BOLD_YELLOW = "\033[1;33m"
BOLD_BLUE = "\033[1;34m"
BOLD_MAGENTA = "\033[1;35m"
BOLD_CYAN = "\033[1;36m"
BOLD_WHITE = "\033[1;37m"

# Background Colors
BG_RED = "\033[41m"
BG_GREEN = "\033[42m"
BG_YELLOW = "\033[43m"
BG_BLUE = "\033[44m"


class ColoredFormatter(logging.Formatter):
    """
    Renders vibrant, color-coded log lines for local development terminals.
    """

    LEVEL_BADGES = {
        logging.DEBUG: f"{BOLD_MAGENTA}DEBUG{RESET}",
        logging.INFO: f"{BOLD_CYAN}INFO {RESET}",
        logging.WARNING: f"{BOLD_YELLOW}WARN {RESET}",
        logging.ERROR: f"{BOLD_RED}ERROR{RESET}",
        logging.CRITICAL: f"{BG_RED}{BOLD_WHITE} CRIT {RESET}",
    }

    def format(self, record: logging.LogRecord) -> str:
        # Time badge
        time_str = f"{FG_GRAY}{self.formatTime(record, self.datefmt)}{RESET}"

        # Level badge
        level_badge = self.LEVEL_BADGES.get(
            record.levelno, f"{BOLD_WHITE}{record.levelname:<5}{RESET}"
        )

        # Logger name
        logger_name = f"{FG_GRAY}[{record.name}]{RESET}"

        # Formatted message
        message = record.getMessage()

        line = f"{time_str} {level_badge} {logger_name} {message}"

        if record.exc_info and record.exc_info[1]:
            line += f"\n{self.formatException(record.exc_info)}"

        return line


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
    - json_output=True  → structured JSON lines (production)
    - json_output=False → beautiful colored terminal output (development)
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    if json_output:
        handler.setFormatter(JSONFormatter(datefmt="%Y-%m-%d %H:%M:%S"))
    else:
        handler.setFormatter(
            ColoredFormatter(datefmt="%H:%M:%S")
        )
    root_logger.addHandler(handler)

    # Suppress verbose noisy internal loggers
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("watchfiles").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("prisma").setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """Returns a named logger for use in application modules."""
    return logging.getLogger(name)
