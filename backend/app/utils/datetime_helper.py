from datetime import datetime


def utc_now() -> datetime:
    """Return the current UTC datetime for timezone-naive database columns."""
    return datetime.utcnow()
