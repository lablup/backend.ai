"""Unit tests for v2 MetricAdapter."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.data.entity.kernel import KernelID
from ai.backend.common.dto.manager.v2.kernel.response import (
    KernelLiveStatInfo,
    KernelLiveStatMetricInfo,
)
from ai.backend.common.types import KernelId
from ai.backend.manager.api.adapters.metric.adapter import MetricAdapter
from ai.backend.manager.clients.prometheus.metric_types import (
    KernelLiveStatBatchResult,
    KernelLiveStatValues,
)
from ai.backend.manager.services.metric.actions.batch_get_kernel_live_stats import (
    BatchGetKernelLiveStatsActionResult,
)


class TestBatchGetKernelLiveStats:
    @pytest.fixture
    def sampled_id(self) -> KernelID:
        return KernelID(uuid4())

    @pytest.fixture
    def unsampled_id(self) -> KernelID:
        return KernelID(uuid4())

    @pytest.fixture
    def processors(self, sampled_id: KernelID) -> MagicMock:
        processors = MagicMock()
        processors.batch_get_kernel_live_stats.run = AsyncMock(
            return_value=BatchGetKernelLiveStatsActionResult(
                stats=KernelLiveStatBatchResult(
                    by_kernel={
                        KernelId(sampled_id): KernelLiveStatValues(
                            instant_current={"mem": "1024"},
                            instant_capacity={"mem": "8192"},
                            max={"mem": "2048"},
                            avg={"mem": "1536"},
                        )
                    }
                )
            )
        )
        return processors

    @pytest.fixture
    def adapter(self, processors: MagicMock) -> MetricAdapter:
        return MetricAdapter(processors)

    async def test_answers_each_kernel_in_order_with_its_metrics(
        self, adapter: MetricAdapter, sampled_id: KernelID, unsampled_id: KernelID
    ) -> None:
        live_stats = await adapter.batch_get_kernel_live_stats([unsampled_id, sampled_id])

        assert live_stats == [
            None,
            KernelLiveStatInfo(
                metrics=[
                    KernelLiveStatMetricInfo(
                        metric_name="mem",
                        current="1024",
                        capacity="8192",
                        pct="12.50",
                        unit_hint="bytes",
                        stats_max="2048",
                        stats_avg="1536",
                        stats_rate="0",
                        stats_diff="0",
                    )
                ]
            ),
        ]

    async def test_no_ids_read_nothing(self, adapter: MetricAdapter, processors: MagicMock) -> None:
        assert await adapter.batch_get_kernel_live_stats([]) == []
        processors.batch_get_kernel_live_stats.run.assert_not_awaited()
