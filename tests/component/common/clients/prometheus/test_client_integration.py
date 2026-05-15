from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta, timezone
from typing import TYPE_CHECKING

import pytest

from ai.backend.common.clients.http_client.client_pool import ClientPool, tcp_client_session_factory
from ai.backend.common.clients.prometheus import (
    ContainerLiveStatQueryBuilder,
    ContainerMetricQueryBuilder,
    LabelMatcher,
    MetricPreset,
    PrometheusClient,
)
from ai.backend.common.dto.clients.prometheus import PrometheusResponse, QueryTimeRange
from ai.backend.common.exception import FailedToGetMetric

if TYPE_CHECKING:
    from ai.backend.testutils.bootstrap import PrometheusContainerFixture

from ai.backend.testutils.bootstrap import prometheus_container  # noqa: F401


@pytest.fixture
async def prometheus_client(
    prometheus_container: PrometheusContainerFixture,  # noqa: F811
) -> AsyncIterator[PrometheusClient]:
    hostport = prometheus_container[1]
    pool = ClientPool(tcp_client_session_factory)
    client = PrometheusClient(
        endpoint=f"http://{hostport.host}:{hostport.port}/api/v1/",
        client_pool=pool,
        container_metric_query_builder=ContainerMetricQueryBuilder("1m"),
        container_live_stat_query_builder=ContainerLiveStatQueryBuilder("1m"),
    )
    try:
        yield client
    finally:
        await pool.close()


@pytest.fixture
def up_metric_preset() -> MetricPreset:
    return MetricPreset(
        template="up{{{labels}}}",
        labels={"job": LabelMatcher.exact("prometheus")},
        group_by=frozenset(),
    )


class TestQueryRangeTimestampFormats:
    """Regression tests for BA-5766: Prometheus rejects naive datetime isoformat."""

    async def test_unix_timestamp_succeeds(
        self,
        prometheus_client: PrometheusClient,
        up_metric_preset: MetricPreset,
    ) -> None:
        now = datetime.now(tz=UTC)
        time_range = QueryTimeRange(
            start=str(now.timestamp() - 60),
            end=str(now.timestamp()),
            step="15s",
        )

        result = await prometheus_client._query_range(up_metric_preset, time_range)

        assert isinstance(result, PrometheusResponse)
        assert result.status == "success"
        assert result.data.result_type == "matrix"

    async def test_naive_datetime_isoformat_rejected(
        self,
        prometheus_client: PrometheusClient,
        up_metric_preset: MetricPreset,
    ) -> None:
        """Regression: naive datetime.isoformat() produces a string without timezone
        suffix (e.g., '2026-04-16T23:00:00') that Prometheus cannot parse."""
        time_range = QueryTimeRange(
            start="2026-04-16T23:00:00",
            end="2026-04-16T23:15:00",
            step="60s",
        )

        with pytest.raises(FailedToGetMetric, match="cannot parse"):
            await prometheus_client._query_range(up_metric_preset, time_range)

    async def test_timezone_aware_datetime_isoformat_succeeds(
        self,
        prometheus_client: PrometheusClient,
        up_metric_preset: MetricPreset,
    ) -> None:
        """Timezone-aware RFC3339 datetimes should be accepted by Prometheus."""
        kst = timezone(timedelta(hours=9))
        end = datetime.now(tz=kst)
        start = end - timedelta(minutes=1)

        time_range = QueryTimeRange(
            start=start.isoformat(),
            end=end.isoformat(),
            step="15s",
        )

        result = await prometheus_client._query_range(up_metric_preset, time_range)

        assert isinstance(result, PrometheusResponse)
        assert result.status == "success"
        assert result.data.result_type == "matrix"
