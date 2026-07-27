from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.types import KernelAggregationMode, ResourceSlot, SessionId
from ai.backend.manager.data.metric.types import (
    SessionUtilizationMetricResult,
    SessionUtilizationMetricThreshold,
)
from ai.backend.manager.data.resource_slot.types import ResourceAllocationAggregate
from ai.backend.manager.repositories.metric.repository import MetricRepository
from ai.backend.manager.repositories.metric.types import SessionUtilizationMetricQuery
from ai.backend.manager.repositories.session.repository import SessionRepository
from ai.backend.manager.services.metric.actions.session_utilization import (
    SessionUtilizationAction,
)
from ai.backend.manager.services.metric.service import MetricService

_NOW = datetime(2026, 7, 25, 12, tzinfo=UTC)


class TestQuerySessionUtilization:
    @pytest.fixture
    def metric_repository(self) -> MagicMock:
        repository = MagicMock(spec=MetricRepository)
        repository.query_session_utilization_metrics = AsyncMock()
        return repository

    @pytest.fixture
    def session_repository(self) -> MagicMock:
        repository = MagicMock(spec=SessionRepository)
        repository.batch_get_resource_allocation_by_session = AsyncMock()
        return repository

    @pytest.fixture
    def service(
        self,
        metric_repository: MagicMock,
        session_repository: MagicMock,
    ) -> MetricService:
        return MetricService(metric_repository, session_repository)

    @pytest.fixture
    def cpu_allocation(self) -> ResourceAllocationAggregate:
        slots = ResourceSlot({"cpu": 1})
        return ResourceAllocationAggregate(
            requested=slots,
            used=slots,
            allocated=ResourceSlot(),
        )

    async def test_queries_sessions_in_one_request(
        self,
        service: MetricService,
        metric_repository: MagicMock,
        session_repository: MagicMock,
        cpu_allocation: ResourceAllocationAggregate,
    ) -> None:
        first_session_id = SessionId(uuid4())
        second_session_id = SessionId(uuid4())
        threshold = SessionUtilizationMetricThreshold(
            metric_name="cpu_util",
            time_window_seconds=None,
            threshold=Decimal("10"),
            kernel_aggregation=KernelAggregationMode.AVERAGE,
        )
        session_repository.batch_get_resource_allocation_by_session.return_value = {
            first_session_id: cpu_allocation,
            second_session_id: cpu_allocation,
        }
        metric_repository.query_session_utilization_metrics.return_value = (
            SessionUtilizationMetricResult(
                by_session={
                    first_session_id: Decimal("5"),
                    second_session_id: Decimal("15"),
                }
            )
        )

        result = await service.query_session_utilization(
            SessionUtilizationAction(
                thresholds=[threshold],
                session_ids=[first_session_id, second_session_id],
                evaluation_time=_NOW,
            )
        )

        session_repository.batch_get_resource_allocation_by_session.assert_awaited_once_with([
            first_session_id,
            second_session_id,
        ])
        metric_repository.query_session_utilization_metrics.assert_awaited_once_with(
            SessionUtilizationMetricQuery(
                metric_name="cpu_util",
                kernel_aggregation=KernelAggregationMode.AVERAGE,
                time_window_seconds=None,
                session_ids=[first_session_id, second_session_id],
                evaluation_time=_NOW,
            )
        )
        assert result.observations_by_session[first_session_id][0].entry == threshold
        assert result.observations_by_session[first_session_id][0].value == 5
        assert result.observations_by_session[second_session_id][0].value == 15

    async def test_infers_custom_accelerator_resource_from_metric_name(
        self,
        service: MetricService,
        metric_repository: MagicMock,
        session_repository: MagicMock,
    ) -> None:
        session_id = SessionId(uuid4())
        accelerator_slots = ResourceSlot({"neuron.device": 1})
        threshold = SessionUtilizationMetricThreshold(
            metric_name="neuron_util",
            time_window_seconds=None,
            threshold=Decimal("10"),
            kernel_aggregation=KernelAggregationMode.AVERAGE,
        )
        session_repository.batch_get_resource_allocation_by_session.return_value = {
            session_id: ResourceAllocationAggregate(
                requested=accelerator_slots,
                used=accelerator_slots,
                allocated=ResourceSlot(),
            )
        }
        metric_repository.query_session_utilization_metrics.return_value = (
            SessionUtilizationMetricResult(by_session={session_id: Decimal("5")})
        )

        result = await service.query_session_utilization(
            SessionUtilizationAction(
                thresholds=[threshold],
                session_ids=[session_id],
                evaluation_time=_NOW,
            )
        )

        metric_repository.query_session_utilization_metrics.assert_awaited_once()
        query = metric_repository.query_session_utilization_metrics.await_args.args[0]
        assert query.metric_name == "neuron_util"
        assert result.observations_by_session[session_id][0].value == 5

    async def test_queries_thresholds_with_different_time_windows_separately(
        self,
        service: MetricService,
        metric_repository: MagicMock,
        session_repository: MagicMock,
    ) -> None:
        session_id = SessionId(uuid4())
        slots = ResourceSlot({"cpu": 1, "neuron.device": 1})
        session_repository.batch_get_resource_allocation_by_session.return_value = {
            session_id: ResourceAllocationAggregate(
                requested=slots,
                used=slots,
                allocated=ResourceSlot(),
            )
        }
        metric_repository.query_session_utilization_metrics.return_value = (
            SessionUtilizationMetricResult(by_session={session_id: Decimal("5")})
        )

        await service.query_session_utilization(
            SessionUtilizationAction(
                thresholds=[
                    SessionUtilizationMetricThreshold(
                        metric_name="cpu_util",
                        time_window_seconds=None,
                        threshold=Decimal("10"),
                        kernel_aggregation=KernelAggregationMode.AVERAGE,
                    ),
                    SessionUtilizationMetricThreshold(
                        metric_name="neuron_util",
                        time_window_seconds=300,
                        threshold=Decimal("10"),
                        kernel_aggregation=KernelAggregationMode.AVERAGE,
                    ),
                ],
                session_ids=[session_id],
                evaluation_time=_NOW,
            )
        )

        assert metric_repository.query_session_utilization_metrics.await_count == 2
        queried_windows = [
            call.args[0].time_window_seconds
            for call in metric_repository.query_session_utilization_metrics.await_args_list
        ]
        assert queried_windows == [None, 300]

    async def test_missing_metric_value_returns_unknown(
        self,
        service: MetricService,
        metric_repository: MagicMock,
        session_repository: MagicMock,
        cpu_allocation: ResourceAllocationAggregate,
    ) -> None:
        session_id = SessionId(uuid4())
        session_repository.batch_get_resource_allocation_by_session.return_value = {
            session_id: cpu_allocation
        }
        metric_repository.query_session_utilization_metrics.return_value = (
            SessionUtilizationMetricResult(by_session={})
        )

        result = await service.query_session_utilization(
            SessionUtilizationAction(
                thresholds=[
                    SessionUtilizationMetricThreshold(
                        metric_name="cpu_util",
                        time_window_seconds=None,
                        threshold=Decimal("10"),
                        kernel_aggregation=KernelAggregationMode.AVERAGE,
                    )
                ],
                session_ids=[session_id],
                evaluation_time=_NOW,
            )
        )

        assert result.observations_by_session == {}

    async def test_converts_memory_to_percentage(
        self,
        service: MetricService,
        metric_repository: MagicMock,
        session_repository: MagicMock,
    ) -> None:
        session_id = SessionId(uuid4())
        memory_slots = ResourceSlot({"mem": 1024})
        session_repository.batch_get_resource_allocation_by_session.return_value = {
            session_id: ResourceAllocationAggregate(
                requested=memory_slots,
                used=memory_slots,
                allocated=ResourceSlot(),
            )
        }
        metric_repository.query_session_utilization_metrics.return_value = (
            SessionUtilizationMetricResult(by_session={session_id: Decimal("512")})
        )

        result = await service.query_session_utilization(
            SessionUtilizationAction(
                thresholds=[
                    SessionUtilizationMetricThreshold(
                        metric_name="mem",
                        time_window_seconds=None,
                        threshold=Decimal("60"),
                        kernel_aggregation=KernelAggregationMode.AVERAGE,
                    )
                ],
                session_ids=[session_id],
                evaluation_time=_NOW,
            )
        )

        assert result.observations_by_session[session_id][0].value == 50

    async def test_empty_sessions_skip_repositories(
        self,
        service: MetricService,
        metric_repository: MagicMock,
        session_repository: MagicMock,
    ) -> None:
        result = await service.query_session_utilization(
            SessionUtilizationAction(
                thresholds=[],
                session_ids=[],
                evaluation_time=_NOW,
            )
        )

        assert result.observations_by_session == {}
        session_repository.batch_get_resource_allocation_by_session.assert_not_awaited()
        metric_repository.query_session_utilization_metrics.assert_not_awaited()
