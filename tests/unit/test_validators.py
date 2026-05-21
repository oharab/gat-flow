"""Unit tests for input validation and parsing helpers."""

from datetime import UTC, datetime
from pathlib import Path

import click
import pytest

from validators import parse_user_datetime, safe_env_path, validate_email


class TestValidateEmail:
    """Tests for validate_email()."""

    @pytest.mark.parametrize(
        "addr",
        [
            "user@example.com",
            "first.last@sub.example.co.uk",
            "user+tag@example.com",
            "user_name@example.com",
            "u@x.io",
            "123@456.com",
        ],
    )
    def test_accepts_valid_addresses(self, addr: str) -> None:
        assert validate_email(addr) == addr

    @pytest.mark.parametrize(
        "addr",
        [
            "",
            "not-an-email",
            "missing@tld",
            "@example.com",
            "user@",
            "user @example.com",
            "user@example",
            "user@@example.com",
        ],
    )
    def test_rejects_invalid_addresses(self, addr: str) -> None:
        with pytest.raises(click.ClickException) as excinfo:
            validate_email(addr)
        assert "Invalid email address" in str(excinfo.value.message)


class TestSafeEnvPath:
    """Tests for safe_env_path()."""

    def test_accepts_path_inside_base(self, tmp_path: Path) -> None:
        target = tmp_path / "config.env"
        target.touch()
        assert safe_env_path(str(target), base=tmp_path) == target.resolve()

    def test_accepts_relative_path_inside_base(self, tmp_path: Path) -> None:
        target = tmp_path / "sub" / "config.env"
        target.parent.mkdir()
        target.touch()
        result = safe_env_path(str(target), base=tmp_path)
        assert result == target.resolve()

    def test_rejects_absolute_path_outside_base(self, tmp_path: Path) -> None:
        outside = tmp_path.parent / "elsewhere.env"
        with pytest.raises(click.ClickException) as excinfo:
            safe_env_path(str(outside), base=tmp_path)
        assert "outside the project directory" in str(excinfo.value.message)

    def test_rejects_parent_traversal(self, tmp_path: Path) -> None:
        traversal = f"{tmp_path}/../escape.env"
        with pytest.raises(click.ClickException):
            safe_env_path(traversal, base=tmp_path)

    def test_rejects_system_path(self, tmp_path: Path) -> None:
        with pytest.raises(click.ClickException):
            safe_env_path("/etc/passwd", base=tmp_path)

    def test_returns_path_even_if_file_does_not_exist(self, tmp_path: Path) -> None:
        # safe_env_path resolves the path without requiring it to exist —
        # callers handle missing files separately.
        nonexistent = tmp_path / "new.env"
        assert safe_env_path(str(nonexistent), base=tmp_path) == nonexistent.resolve()


class TestParseUserDatetime:
    """Tests for parse_user_datetime()."""

    def test_parses_date_only(self) -> None:
        result = parse_user_datetime("2026-06-15", UTC)
        assert result == datetime(2026, 6, 15, 0, 0, tzinfo=UTC)

    def test_parses_date_and_time(self) -> None:
        result = parse_user_datetime("2026-06-15 09:30", UTC)
        assert result == datetime(2026, 6, 15, 9, 30, tzinfo=UTC)

    def test_attaches_provided_timezone(self) -> None:
        result = parse_user_datetime("2026-06-15 09:30", UTC)
        assert result is not None
        assert result.tzinfo == UTC

    @pytest.mark.parametrize(
        "value",
        [
            "",
            "not-a-date",
            "2026/06/15",
            "15-06-2026",
            "2026-13-01",  # invalid month
            "2026-06-15T09:30",  # ISO with T separator not supported
            "2026-06-15 25:00",  # invalid hour
            "2026-06-15 09:60",  # invalid minute
        ],
    )
    def test_returns_none_for_invalid_input(self, value: str) -> None:
        assert parse_user_datetime(value, UTC) is None

    def test_time_format_takes_precedence_when_both_could_match(self) -> None:
        # "2026-06-15 09:30" matches the datetime format, not the date-only one
        result = parse_user_datetime("2026-06-15 09:30", UTC)
        assert result is not None
        assert result.hour == 9
        assert result.minute == 30
