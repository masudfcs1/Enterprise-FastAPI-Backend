"""
Request and response logging middleware with vibrant color-coding and latency metrics.
"""

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("api")

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[90m"

# Color-coded HTTP method badges
METHOD_COLORS = {
    "GET": "\033[1;36mGET   \033[0m",
    "POST": "\033[1;32mPOST  \033[0m",
    "PUT": "\033[1;33mPUT   \033[0m",
    "PATCH": "\033[1;35mPATCH \033[0m",
    "DELETE": "\033[1;31mDELETE\033[0m",
    "OPTIONS": "\033[1;37mOPTION\033[0m",
    "HEAD": "\033[1;34mHEAD  \033[0m",
}


def _format_status(status_code: int) -> str:
    """Format HTTP status code with color highlighting."""
    if 200 <= status_code < 300:
        return f"\033[1;32m{status_code} OK\033[0m"
    elif 300 <= status_code < 400:
        return f"\033[1;34m{status_code}\033[0m"
    elif 400 <= status_code < 500:
        return f"\033[1;33m{status_code} Client Error\033[0m"
    else:
        return f"\033[1;41;97m {status_code} Server Error \033[0m"


def _format_duration(ms: float) -> str:
    """Color-code execution time (green=fast, yellow=medium, red=slow)."""
    if ms < 50:
        return f"\033[32m{ms:.2f}ms\033[0m"
    elif ms < 200:
        return f"\033[33m{ms:.2f}ms\033[0m"
    else:
        return f"\033[1;31m{ms:.2f}ms\033[0m"


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start = time.perf_counter()
        request_id: str = getattr(request.state, "request_id", "N/A")
        short_id = request_id[:8] if len(request_id) > 8 else request_id
        method_badge = METHOD_COLORS.get(request.method, f"\033[1m{request.method:<6}\033[0m")
        path = request.url.path

        # Log incoming request
        logger.info(
            f"\033[1;36m-->\033[0m {method_badge} \033[1m{path}\033[0m {DIM}[{short_id}]{RESET}"
        )

        response: Response = await call_next(request)

        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        status_badge = _format_status(response.status_code)
        duration_badge = _format_duration(elapsed_ms)
        arrow = "\033[1;32m<--\033[0m" if response.status_code < 400 else "\033[1;31m<--\033[0m"

        # Log completed response
        logger.info(
            f"{arrow} {method_badge} \033[1m{path}\033[0m {status_badge} in {duration_badge} {DIM}[{short_id}]{RESET}"
        )
        return response
