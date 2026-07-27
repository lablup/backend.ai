from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.data.idle_checker.types import (
    UtilizationKernelPolicy,
    UtilizationSpec,
    UtilizationThresholdEntry,
)
from ai.backend.common.types import ResourceSlot, SessionId
from ai.backend.manager.data.metric.types import SessionUtilizationMetricResult
from ai.backend.manager.data.resource_slot.types import ResourceAllocationAggregate
from ai.backend.manager.repositories.metric.repository import MetricRepository
from ai.backend.manager.repositories.metric.types import SessionUtilizationMetricQuery
from ai.backend.manager.repositories.session.repository import SessionRepository
from ai.backend.manager.services.metric.actions.session_utilization import (
    SessionUtilizationBatchAction,
    SessionUtilizationCheck,
)
from ai.backend.manager.services.metric.service import MetricService

_NOW = datetime(2026, 7, 25, 12, tzinfo=UTC)


def _check(
    session_id: SessionId,
    *,
    metric_name: str = "cpu_util",
    threshold: str = "10",
    duration_seconds: int = 1800,
    time_window_seconds: int | None = None,
) -> SessionUtilizationCheck:
    return SessionUtilizationCheck(
        spec=UtilizationSpec(
            max_underutilized_duration_seconds=duration_seconds,
            thresholds=[
                UtilizationThresholdEntry(
                    metric_name=metric_name,
                    time_window_seconds=time_window_seconds,
                    threshold=Decimal(threshold),
                    kernel_policy=UtilizationKernelPolicy.AVERAGE,
                )
            ],
        ),
        session_ids=[session_id],
    )


class TestQuerySessionUtilizationBatch:
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
    def allocation(self) -> ResourceAllocationAggregate:
        slots = ResourceSlot({"cpu": 1})
        return ResourceAllocationAggregate(
            requested=slots,
            used=slots,
            allocated=ResourceSlot(),
        )

    async def test_batches_same_query_shape(
        self,
        service: MetricService,
        metric_repository: MagicMock,
        session_repository: MagicMock,
        allocation: ResourceAllocationAggregate,
    ) -> None:
        first_session_id = SessionId(uuid4())
        second_session_id = SessionId(uuid4())
        session_repository.batch_get_resource_allocation_by_session.return_value = {
            first_session_id: allocation,
            second_session_id: allocation,
        }
        metric_repository.query_session_utilization_metrics.return_value = (
            SessionUtilizationMetricResult(
                by_session={
                    first_session_id: Decimal("5"),
                    second_session_id: Decimal("15"),
                }
            )
        )

        result = await service.query_session_utilization_batch(
            SessionUtilizationBatchAction(
                checks=(
                    _check(first_session_id),
                    _check(second_session_id, threshold="20"),
                ),
                evaluation_time=_NOW,
            )
        )

        session_repository.batch_get_resource_allocation_by_session.assert_awaited_once()
        fetched_session_ids = (
            session_repository.batch_get_resource_allocation_by_session.await_args.args[0]
        )
        assert set(fetched_session_ids) == {first_session_id, second_session_id}
        metric_repository.query_session_utilization_metrics.assert_awaited_once()
        query = metric_repository.query_session_utilization_metrics.await_args.args[0]
        assert isinstance(query, SessionUtilizationMetricQuery)
        assert set(query.session_ids) == {first_session_id, second_session_id}
        assert result.observations_by_check[0][first_session_id][0].value == 5
        assert result.observations_by_check[1][second_session_id][0].value == 15

    async def test_infers_custom_accelerator_resource_from_metric_name(
        self,
        service: MetricService,
        metric_repository: MagicMock,
        session_repository: MagicMock,
    ) -> None:
        session_id = SessionId(uuid4())
        accelerator_slots = ResourceSlot({"neuron.device": 1})
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

        result = await service.query_session_utilization_batch(
            SessionUtilizationBatchAction(
                checks=[
                    _check(
                        session_id,
                        metric_name="neuron_util",
                    )
                ],
                evaluation_time=_NOW,
            )
        )

        metric_repository.query_session_utilization_metrics.assert_awaited_once()
        query = metric_repository.query_session_utilization_metrics.await_args.args[0]
        assert query.metric_name == "neuron_util"
        assert result.observations_by_check[0][session_id][0].value == 5

    async def test_batches_checks_with_different_idle_durations(
        self,
        service: MetricService,
        metric_repository: MagicMock,
        session_repository: MagicMock,
        allocation: ResourceAllocationAggregate,
    ) -> None:
        session_id = SessionId(uuid4())
        session_repository.batch_get_resource_allocation_by_session.return_value = {
            session_id: allocation
        }
        metric_repository.query_session_utilization_metrics.return_value = (
            SessionUtilizationMetricResult(by_session={session_id: Decimal("5")})
        )

        result = await service.query_session_utilization_batch(
            SessionUtilizationBatchAction(
                checks=(
                    _check(session_id, duration_seconds=900),
                    _check(session_id, duration_seconds=1800),
                ),
                evaluation_time=_NOW,
            )
        )

        metric_repository.query_session_utilization_metrics.assert_awaited_once()
        assert result.observations_by_check[0][session_id][0].value == 5
        assert result.observations_by_check[1][session_id][0].value == 5

    async def test_queries_different_time_windows_separately(
        self,
        service: MetricService,
        metric_repository: MagicMock,
        session_repository: MagicMock,
        allocation: ResourceAllocationAggregate,
    ) -> None:
        session_id = SessionId(uuid4())
        session_repository.batch_get_resource_allocation_by_session.return_value = {
            session_id: allocation
        }
        metric_repository.query_session_utilization_metrics.return_value = (
            SessionUtilizationMetricResult(by_session={session_id: Decimal("5")})
        )

        await service.query_session_utilization_batch(
            SessionUtilizationBatchAction(
                checks=(
                    _check(session_id, time_window_seconds=None),
                    _check(session_id, time_window_seconds=300),
                ),
                evaluation_time=_NOW,
            )
        )

        assert metric_repository.query_session_utilization_metrics.await_count == 2
        queried_windows = {
            call.args[0].time_window_seconds
            for call in metric_repository.query_session_utilization_metrics.await_args_list
        }
        assert queried_windows == {None, 300}
