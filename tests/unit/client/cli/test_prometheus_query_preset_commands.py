from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

import click
import pytest

from ai.backend.client.cli.v2.prometheus_query_preset.commands import prometheus_timestamp


class TestPrometheusTimestampParamType:
    """Tests for Prometheus CLI timestamp parsing."""

    def test_parse_timezone_aware_iso8601(self) -> None:
        parsed = prometheus_timestamp.convert("2026-04-16T23:00:00+09:00", None, None)

        assert parsed == datetime(2026, 4, 16, 23, 0, 0, tzinfo=timezone(timedelta(hours=9)))

    def test_parse_utc_z_suffix(self) -> None:
        parsed = prometheus_timestamp.convert("2026-04-16T14:00:00Z", None, None)

        assert parsed == datetime(2026, 4, 16, 14, 0, 0, tzinfo=UTC)

    def test_parse_unix_timestamp(self) -> None:
        parsed = prometheus_timestamp.convert("1713372000", None, None)

        assert parsed == datetime.fromtimestamp(1713372000, tz=UTC)

    def test_reject_naive_datetime(self) -> None:
        with pytest.raises(click.BadParameter, match="timezone-aware ISO8601 datetime"):
            prometheus_timestamp.convert("2026-04-16T23:00:00", None, None)
