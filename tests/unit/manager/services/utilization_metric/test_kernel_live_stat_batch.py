from unittest.mock import AsyncMock, Mock
from uuid import UUID

import pytest

from ai.backend.common.clients.prometheus.types import MetricValue, ValueType
from ai.backend.common.exception import PrometheusConnectionError
from ai.backend.common.types import KernelId
from ai.backend.manager.services.metric.actions.live_stat import QueryKernelLiveStatAction
from ai.backend.manager.services.metric.root_service import UtilizationMetricService


class TestKernelLiveStatBatch:
    """Test the kernel live stat query pipeline via service → repository."""

    @pytest.fixture()
    def mock_metric_repository(self) -> Mock:
        return Mock()

    @pytest.fixture()
    def metric_service(self, mock_metric_repository: Mock) -> UtilizationMetricService:
        return UtilizationMetricService(
            prometheus_client=Mock(),
            timewindow="1m",
            metric_repository=mock_metric_repository,
        )

    async def test_collects_and_assembles_batch_result(
        self,
        mock_metric_repository: Mock,
        metric_service: UtilizationMetricService,
    ) -> None:
        """Service assembles KernelLiveStatBatchResult from repository response."""
        kid = KernelId(UUID("12345678-1234-5678-1234-567812345678"))

        mock_metric_repository.query_kernel_live_stats = AsyncMock(
            return_value={
                kid: [
                    MetricValue(
                        metric_name="mem", value_type=ValueType.CURRENT, value="5368709120"
                    ),
                    MetricValue(
                        metric_name="mem", value_type=ValueType.CAPACITY, value="8589934592"
                    ),
                    MetricValue(metric_name="cpu_util", value_type=ValueType.CURRENT, value="50.0"),
                ],
            }
        )

        result = await metric_service.query_kernel_live_stat_batch(
            QueryKernelLiveStatAction(kernel_ids=[kid])
        )
        entry = result.stats.entries[kid]
        values_by_key = {(v.metric_name, v.value_type): v.value for v in entry.values}

        assert values_by_key[("mem", ValueType.CURRENT)] == "5368709120"
        assert values_by_key[("mem", ValueType.CAPACITY)] == "8589934592"
        assert values_by_key[("cpu_util", ValueType.CURRENT)] == "50.0"

    async def test_empty_kernel_returns_empty_entry(
        self,
        mock_metric_repository: Mock,
        metric_service: UtilizationMetricService,
    ) -> None:
        """A kernel with no Prometheus samples must yield an empty entry."""
        empty_kernel = KernelId(UUID("00000000-0000-0000-0000-000000000000"))
        mock_metric_repository.query_kernel_live_stats = AsyncMock(return_value={})

        result = await metric_service.query_kernel_live_stat_batch(
            QueryKernelLiveStatAction(kernel_ids=[empty_kernel])
        )
        entry = result.stats.entries[empty_kernel]
        assert entry.values == []

    async def test_prometheus_connection_error_returns_empty_entries(
        self,
        mock_metric_repository: Mock,
        metric_service: UtilizationMetricService,
    ) -> None:
        """When Prometheus is unreachable, every kernel_id maps to an empty entry."""
        kid = KernelId(UUID("12345678-1234-5678-1234-567812345678"))
        mock_metric_repository.query_kernel_live_stats = AsyncMock(
            side_effect=PrometheusConnectionError("unreachable")
        )

        result = await metric_service.query_kernel_live_stat_batch(
            QueryKernelLiveStatAction(kernel_ids=[kid])
        )
        entry = result.stats.entries[kid]
        assert entry.values == []

    async def test_empty_kernel_ids_short_circuits(
        self,
        mock_metric_repository: Mock,
        metric_service: UtilizationMetricService,
    ) -> None:
        """No kernel_ids -> empty result, no repository query issued."""
        result = await metric_service.query_kernel_live_stat_batch(
            QueryKernelLiveStatAction(kernel_ids=[])
        )
        assert result.stats.entries == {}

    async def test_multiple_kernels_grouped_correctly(
        self,
        mock_metric_repository: Mock,
        metric_service: UtilizationMetricService,
    ) -> None:
        """Values from multiple kernels are grouped into separate entries."""
        kid1 = KernelId(UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"))
        kid2 = KernelId(UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"))

        mock_metric_repository.query_kernel_live_stats = AsyncMock(
            return_value={
                kid1: [
                    MetricValue(metric_name="mem", value_type=ValueType.CURRENT, value="100"),
                ],
                kid2: [
                    MetricValue(metric_name="mem", value_type=ValueType.CURRENT, value="200"),
                ],
            }
        )

        result = await metric_service.query_kernel_live_stat_batch(
            QueryKernelLiveStatAction(kernel_ids=[kid1, kid2])
        )

        values1 = {
            (v.metric_name, v.value_type): v.value for v in result.stats.entries[kid1].values
        }
        values2 = {
            (v.metric_name, v.value_type): v.value for v in result.stats.entries[kid2].values
        }
        assert values1[("mem", ValueType.CURRENT)] == "100"
        assert values2[("mem", ValueType.CURRENT)] == "200"
