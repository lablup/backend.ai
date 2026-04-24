from unittest.mock import AsyncMock, Mock
from uuid import UUID

import pytest

from ai.backend.common.clients.prometheus.types import MetricValue, ValueType
from ai.backend.common.types import KernelId
from ai.backend.manager.data.metric.types import KernelLiveStatBatchResult
from ai.backend.manager.services.metric.actions.live_stat import ContainerLiveStatAction
from ai.backend.manager.services.metric.service import MetricService


class TestKernelLiveStatBatch:
    """Test the kernel live stat query pipeline via service → repository."""

    @pytest.fixture()
    def mock_metric_repository(self) -> Mock:
        return Mock()

    @pytest.fixture()
    def metric_service(self, mock_metric_repository: Mock) -> MetricService:
        return MetricService(
            metric_repository=mock_metric_repository,
        )

    async def test_collects_and_assembles_batch_result(
        self,
        mock_metric_repository: Mock,
        metric_service: MetricService,
    ) -> None:
        """Service assembles KernelLiveStatBatchResult from repository response."""
        kid = KernelId(UUID("12345678-1234-5678-1234-567812345678"))

        batch_result = KernelLiveStatBatchResult.from_metric_values(
            [kid],
            {
                kid: [
                    MetricValue(
                        metric_name="mem", value_type=ValueType.CURRENT, value="5368709120"
                    ),
                    MetricValue(
                        metric_name="mem", value_type=ValueType.CAPACITY, value="8589934592"
                    ),
                    MetricValue(metric_name="cpu_util", value_type=ValueType.CURRENT, value="50.0"),
                ],
            },
        )
        mock_metric_repository.query_container_live_stats = AsyncMock(return_value=batch_result)

        result = await metric_service.query_container_live_stats(
            ContainerLiveStatAction(kernel_ids=[kid])
        )
        entry = result.stats.entries[kid]
        values_by_key = {(v.metric_name, v.value_type): v.value for v in entry.values}

        assert values_by_key[("mem", ValueType.CURRENT)] == "5368709120"
        assert values_by_key[("mem", ValueType.CAPACITY)] == "8589934592"
        assert values_by_key[("cpu_util", ValueType.CURRENT)] == "50.0"

    async def test_empty_kernel_returns_empty_entry(
        self,
        mock_metric_repository: Mock,
        metric_service: MetricService,
    ) -> None:
        """A kernel with no Prometheus samples must yield an empty entry."""
        empty_kernel = KernelId(UUID("00000000-0000-0000-0000-000000000000"))
        batch_result = KernelLiveStatBatchResult.from_metric_values([empty_kernel], {})
        mock_metric_repository.query_container_live_stats = AsyncMock(return_value=batch_result)

        result = await metric_service.query_container_live_stats(
            ContainerLiveStatAction(kernel_ids=[empty_kernel])
        )
        entry = result.stats.entries[empty_kernel]
        assert entry.values == []

    async def test_empty_kernel_ids_returns_empty_result(
        self,
        mock_metric_repository: Mock,
        metric_service: MetricService,
    ) -> None:
        """No kernel_ids -> empty result from repository."""
        batch_result = KernelLiveStatBatchResult.empty([])
        mock_metric_repository.query_container_live_stats = AsyncMock(return_value=batch_result)

        result = await metric_service.query_container_live_stats(
            ContainerLiveStatAction(kernel_ids=[])
        )
        assert result.stats.entries == {}

    async def test_multiple_kernels_grouped_correctly(
        self,
        mock_metric_repository: Mock,
        metric_service: MetricService,
    ) -> None:
        """Values from multiple kernels are grouped into separate entries."""
        kid1 = KernelId(UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"))
        kid2 = KernelId(UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"))

        batch_result = KernelLiveStatBatchResult.from_metric_values(
            [kid1, kid2],
            {
                kid1: [
                    MetricValue(metric_name="mem", value_type=ValueType.CURRENT, value="100"),
                ],
                kid2: [
                    MetricValue(metric_name="mem", value_type=ValueType.CURRENT, value="200"),
                ],
            },
        )
        mock_metric_repository.query_container_live_stats = AsyncMock(return_value=batch_result)

        result = await metric_service.query_container_live_stats(
            ContainerLiveStatAction(kernel_ids=[kid1, kid2])
        )

        values1 = {
            (v.metric_name, v.value_type): v.value for v in result.stats.entries[kid1].values
        }
        values2 = {
            (v.metric_name, v.value_type): v.value for v in result.stats.entries[kid2].values
        }
        assert values1[("mem", ValueType.CURRENT)] == "100"
        assert values2[("mem", ValueType.CURRENT)] == "200"
