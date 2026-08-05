"""Date, markdown, and string formatting helpers."""

from __future__ import annotations

from datetime import datetime, timezone


def format_date(dt: datetime, fmt: str = "%Y-%m-%d") -> str:
    """Format a datetime object to a string.

    Args:
        dt: The datetime to format.
        fmt: The strftime format string.

    Returns:
        Formatted date string.
    """
    return dt.strftime(fmt)


def utc_now() -> datetime:
    """Return the current UTC datetime."""
    return datetime.now(tz=timezone.utc)


def slugify(text: str) -> str:
    """Convert a string to a URL-friendly slug.

    Args:
        text: The input string.

    Returns:
        Lowercased, hyphen-separated slug.
    """
    import re

    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[-\s]+", "-", text)


def truncate(text: str, max_length: int = 80, suffix: str = "...") -> str:
    """Truncate a string to a maximum length.

    Args:
        text: The input string.
        max_length: Maximum allowed length.
        suffix: Suffix to append when truncated.

    Returns:
        Truncated string.
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix
