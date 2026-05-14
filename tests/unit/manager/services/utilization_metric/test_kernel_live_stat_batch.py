from unittest.mock import AsyncMock, Mock
from uuid import UUID

import pytest

from ai.backend.common.clients.prometheus.metric_types import (
    KernelLiveStatBatchResult,
    KernelLiveStatValues,
)
from ai.backend.common.types import KernelId
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

    async def test_passes_raw_result_through(
        self,
        mock_metric_repository: Mock,
        metric_service: MetricService,
    ) -> None:
        """Service simply propagates the repository's raw result."""
        kid = KernelId(UUID("12345678-1234-5678-1234-567812345678"))

        raw = KernelLiveStatBatchResult(
            by_kernel={
                kid: KernelLiveStatValues(
                    instant_current={"mem": "5368709120", "cpu_util": "999"},
                    instant_capacity={"mem": "8589934592"},
                    rate_current={"cpu_util": "50.0"},
                ),
            },
        )
        mock_metric_repository.query_container_live_stats = AsyncMock(return_value=raw)

        result = await metric_service.query_container_live_stats(
            ContainerLiveStatAction(kernel_ids=[kid])
        )

        assert result.stats is raw
        assert result.stats.by_kernel[kid].instant_current["mem"] == "5368709120"
        assert result.stats.by_kernel[kid].rate_current["cpu_util"] == "50.0"

    async def test_empty_kernel_returns_empty_bags(
        self,
        mock_metric_repository: Mock,
        metric_service: MetricService,
    ) -> None:
        """Repository may return an empty result for kernels without samples."""
        empty_kernel = KernelId(UUID("00000000-0000-0000-0000-000000000000"))
        raw = KernelLiveStatBatchResult.empty([empty_kernel])
        mock_metric_repository.query_container_live_stats = AsyncMock(return_value=raw)

        result = await metric_service.query_container_live_stats(
            ContainerLiveStatAction(kernel_ids=[empty_kernel])
        )
        assert result.stats.by_kernel == {empty_kernel: KernelLiveStatValues()}

    async def test_empty_kernel_ids_returns_empty_result(
        self,
        mock_metric_repository: Mock,
        metric_service: MetricService,
    ) -> None:
        """No kernel_ids -> repository hands back an empty result."""
        raw = KernelLiveStatBatchResult.empty([])
        mock_metric_repository.query_container_live_stats = AsyncMock(return_value=raw)

        result = await metric_service.query_container_live_stats(
            ContainerLiveStatAction(kernel_ids=[])
        )
        assert result.stats is raw

    async def test_multiple_kernels_grouped_correctly(
        self,
        mock_metric_repository: Mock,
        metric_service: MetricService,
    ) -> None:
        """Values from multiple kernels remain separated in the result."""
        kid1 = KernelId(UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"))
        kid2 = KernelId(UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"))

        raw = KernelLiveStatBatchResult(
            by_kernel={
                kid1: KernelLiveStatValues(instant_current={"mem": "100"}),
                kid2: KernelLiveStatValues(instant_current={"mem": "200"}),
            },
        )
        mock_metric_repository.query_container_live_stats = AsyncMock(return_value=raw)

        result = await metric_service.query_container_live_stats(
            ContainerLiveStatAction(kernel_ids=[kid1, kid2])
        )

        assert result.stats.by_kernel[kid1].instant_current["mem"] == "100"
        assert result.stats.by_kernel[kid2].instant_current["mem"] == "200"
