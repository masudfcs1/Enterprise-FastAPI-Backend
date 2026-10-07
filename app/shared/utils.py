"""
General-purpose utility helpers.
"""

import math
import uuid


def generate_uuid() -> str:
    """Generate a UUID4 string."""
    return str(uuid.uuid4())


def calculate_total_pages(total: int, size: int) -> int:
    """Calculate total number of pages for pagination."""
    return math.ceil(total / size) if size > 0 else 0
