from typing import Any


def calculate_confidence(sources: list[dict[str, Any]]) -> int:
    """Calculate a 0-100 confidence score based on the number of confirming sources."""
    base = 30
    increment = 12
    score = base + min(len(sources), 6) * increment
    return min(score, 100)
