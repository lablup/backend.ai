from unittest.mock import AsyncMock, Mock
from uuid import UUID

import pytest

from ai.backend.common.clients.prometheus.client import PrometheusClient
from ai.backend.common.dto.clients.prometheus.response import (
    MetricResponse,
    MetricResponseInfo,
    PrometheusQueryData,
    PrometheusResponse,
)
from ai.backend.common.exception import PrometheusConnectionError
from ai.backend.common.types import KernelId
from ai.backend.manager.services.metric.actions.live_stat import KernelLiveStatAction
from ai.backend.manager.services.metric.root_service import UtilizationMetricService
from ai.backend.manager.services.metric.types import ValueType


class TestKernelLiveStatBatch:
    """Test the Prometheus-based kernel live stat query pipeline."""

    @pytest.fixture()
    def mock_prometheus_client(self) -> Mock:
        return Mock(spec=PrometheusClient)

    @pytest.fixture()
    def metric_service(self, mock_prometheus_client: Mock) -> UtilizationMetricService:
        return UtilizationMetricService(
            prometheus_client=mock_prometheus_client,
            timewindow="1m",
            metric_repository=Mock(),
        )

    @staticmethod
    def _sample(
        kernel_id: str,
        metric_name: str,
        value_type: str,
        value: str,
    ) -> MetricResponse:
        return MetricResponse(
            metric=MetricResponseInfo(
                kernel_id=kernel_id,
                container_metric_name=metric_name,
                value_type=value_type,
            ),
            values=[(0.0, value)],
        )

    @staticmethod
    def _response(samples: list[MetricResponse]) -> PrometheusResponse:
        return PrometheusResponse(
            status="success",
            data=PrometheusQueryData(result_type="vector", result=samples),
        )

    async def test_collects_gauge_diff_rate_values(
        self,
        mock_prometheus_client: Mock,
        metric_service: UtilizationMetricService,
    ) -> None:
        """Gauge, diff, and rate values are collected and merged per kernel."""
        kid = KernelId(UUID("12345678-1234-5678-1234-567812345678"))
        kid_str = str(kid)

        mock_prometheus_client.query_instant = AsyncMock(
            side_effect=[
                self._response([
                    self._sample(kid_str, "mem", "current", "5368709120"),
                    self._sample(kid_str, "mem", "capacity", "8589934592"),
                    self._sample(kid_str, "cpu_util", "capacity", "100.0"),
                ]),
                self._response([
                    self._sample(kid_str, "cpu_util", "current", "50.0"),
                ]),
                self._response([
                    self._sample(kid_str, "net_rx", "current", "1024.0"),
                    self._sample(kid_str, "net_tx", "current", "2048.0"),
                ]),
            ]
        )

        result = await metric_service.query_kernel_live_stat_batch(
            KernelLiveStatAction(kernel_ids=[kid])
        )
        entry = result.stats.entries[kid]
        values_by_key = {(v.metric_name, v.value_type): v.value for v in entry.values}

        assert values_by_key[("mem", ValueType.CURRENT)] == "5368709120"
        assert values_by_key[("mem", ValueType.CAPACITY)] == "8589934592"
        assert values_by_key[("cpu_util", ValueType.CURRENT)] == "50.0"
        assert values_by_key[("cpu_util", ValueType.CAPACITY)] == "100.0"
        assert values_by_key[("net_rx", ValueType.CURRENT)] == "1024.0"
        assert values_by_key[("net_tx", ValueType.CURRENT)] == "2048.0"

    async def test_empty_kernel_returns_empty_entry_not_none(
        self,
        mock_prometheus_client: Mock,
        metric_service: UtilizationMetricService,
    ) -> None:
        """A kernel with no Prometheus samples must yield an empty entry, not None."""
        empty_kernel = KernelId(UUID("00000000-0000-0000-0000-000000000000"))
        mock_prometheus_client.query_instant = AsyncMock(
            return_value=self._response([]),
        )

        result = await metric_service.query_kernel_live_stat_batch(
            KernelLiveStatAction(kernel_ids=[empty_kernel])
        )
        entry = result.stats.entries[empty_kernel]
        assert entry.values == []

    async def test_prometheus_connection_error_returns_empty_entries(
        self,
        mock_prometheus_client: Mock,
        metric_service: UtilizationMetricService,
    ) -> None:
        """When Prometheus is unreachable, every kernel_id maps to an empty entry."""
        kid = KernelId(UUID("12345678-1234-5678-1234-567812345678"))
        mock_prometheus_client.query_instant = AsyncMock(
            side_effect=PrometheusConnectionError("unreachable")
        )

        result = await metric_service.query_kernel_live_stat_batch(
            KernelLiveStatAction(kernel_ids=[kid])
        )
        entry = result.stats.entries[kid]
        assert entry.values == []

    async def test_issues_three_prometheus_queries(
        self,
        mock_prometheus_client: Mock,
        metric_service: UtilizationMetricService,
    ) -> None:
        """The batch loader must issue exactly 3 instant queries (GAUGE/DIFF/RATE)."""
        kid = KernelId(UUID("12345678-1234-5678-1234-567812345678"))
        mock_prometheus_client.query_instant = AsyncMock(
            return_value=self._response([]),
        )

        await metric_service.query_kernel_live_stat_batch(KernelLiveStatAction(kernel_ids=[kid]))
        assert mock_prometheus_client.query_instant.await_count == 3

    async def test_rendered_queries_use_regex_matchers(
        self,
        mock_prometheus_client: Mock,
        metric_service: UtilizationMetricService,
    ) -> None:
        kid = KernelId(UUID("12345678-1234-5678-1234-567812345678"))
        mock_prometheus_client.query_instant = AsyncMock(
            return_value=self._response([]),
        )

        await metric_service.query_kernel_live_stat_batch(KernelLiveStatAction(kernel_ids=[kid]))

        rendered_queries = [
            call.args[0].render() for call in mock_prometheus_client.query_instant.await_args_list
        ]
        assert len(rendered_queries) == 3
        assert all('kernel_id=~"' in query for query in rendered_queries)
        assert any('container_metric_name=~"cpu_util"' in query for query in rendered_queries)
        assert any('container_metric_name=~"net_rx|net_tx"' in query for query in rendered_queries)

    async def test_empty_kernel_ids_short_circuits(
        self,
        mock_prometheus_client: Mock,
        metric_service: UtilizationMetricService,
    ) -> None:
        """No kernel_ids -> empty result, no Prometheus query issued."""
        result = await metric_service.query_kernel_live_stat_batch(
            KernelLiveStatAction(kernel_ids=[])
        )
        assert result.stats.entries == {}
        mock_prometheus_client.query_instant.assert_not_called()

    async def test_multiple_kernels_grouped_correctly(
        self,
        mock_prometheus_client: Mock,
        metric_service: UtilizationMetricService,
    ) -> None:
        """Values from multiple kernels are grouped into separate entries."""
        kid1 = KernelId(UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"))
        kid2 = KernelId(UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"))

        mock_prometheus_client.query_instant = AsyncMock(
            side_effect=[
                self._response([
                    self._sample(str(kid1), "mem", "current", "100"),
                    self._sample(str(kid2), "mem", "current", "200"),
                ]),
                self._response([]),
                self._response([]),
            ]
        )

        result = await metric_service.query_kernel_live_stat_batch(
            KernelLiveStatAction(kernel_ids=[kid1, kid2])
        )

        values1 = {
            (v.metric_name, v.value_type): v.value for v in result.stats.entries[kid1].values
        }
        values2 = {
            (v.metric_name, v.value_type): v.value for v in result.stats.entries[kid2].values
        }
        assert values1[("mem", ValueType.CURRENT)] == "100"
        assert values2[("mem", ValueType.CURRENT)] == "200"
