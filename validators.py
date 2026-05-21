"""Input validation and parsing helpers for the CLI."""

import re
from datetime import datetime, tzinfo
from pathlib import Path

import click

_EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
_DATE_FORMATS = ("%Y-%m-%d %H:%M", "%Y-%m-%d")


def validate_email(addr: str) -> str:
    """Validate an email address, raising ClickException on failure."""
    if not _EMAIL_RE.match(addr):
        raise click.ClickException(f"Invalid email address: {addr!r}")
    return addr


def safe_env_path(file: str, base: Path | None = None) -> Path:
    """Resolve a user-supplied env file path and reject paths outside ``base``.

    ``base`` defaults to the current working directory.
    """
    root = (base or Path.cwd()).resolve()
    resolved = Path(file).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as e:
        raise click.ClickException(
            f"Refusing to access {file!r}: path is outside the project directory.",
        ) from e
    return resolved


def parse_user_datetime(value: str, tz: tzinfo) -> datetime | None:
    """Parse a user-supplied date or date-time string and attach ``tz``.

    Accepts ``YYYY-MM-DD HH:MM`` or ``YYYY-MM-DD``. Returns ``None`` on
    invalid input.
    """
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).replace(tzinfo=tz)
        except ValueError:
            continue
    return None
