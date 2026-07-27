import logging
from collections import defaultdict
from collections.abc import Sequence
from decimal import Decimal

from ai.backend.common.types import SessionId
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.metric.types import SessionUtilizationMetricThreshold
from ai.backend.manager.data.resource_slot.types import ResourceAllocationAggregate
from ai.backend.manager.repositories.metric.repository import MetricRepository
from ai.backend.manager.repositories.metric.types import SessionUtilizationMetricQuery
from ai.backend.manager.repositories.session.repository import SessionRepository

from .actions.container import (
    ContainerMetricAction,
    ContainerMetricActionResult,
    ContainerMetricMetadataAction,
    ContainerMetricMetadataActionResult,
)
from .actions.live_stat import ContainerLiveStatAction, ContainerLiveStatActionResult
from .actions.session_utilization import (
    SessionUtilizationAction,
    SessionUtilizationActionResult,
    SessionUtilizationObservation,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

_RESOURCE_METRIC_SUFFIXES = ("_util", "_mem", "_used")


class MetricService:
    _metric_repository: MetricRepository
    _session_repository: SessionRepository

    def __init__(
        self,
        metric_repository: MetricRepository,
        session_repository: SessionRepository,
    ) -> None:
        self._metric_repository = metric_repository
        self._session_repository = session_repository

    def _to_utilization_percentage(
        self,
        metric_name: str,
        value: Decimal,
        allocation: ResourceAllocationAggregate,
    ) -> Decimal | None:
        if metric_name != "mem":
            return value
        occupied_memory = allocation.used.get("mem")
        if occupied_memory is None or occupied_memory <= 0:
            return None
        return value / occupied_memory * 100

    def _get_applicable_session_ids(
        self,
        threshold: SessionUtilizationMetricThreshold,
        session_ids: Sequence[SessionId],
        resources_by_session: dict[SessionId, set[str]],
    ) -> list[SessionId]:
        resource_name = threshold.metric_name
        for suffix in _RESOURCE_METRIC_SUFFIXES:
            if resource_name.endswith(suffix):
                resource_name = resource_name.removesuffix(suffix)
                break

        applicable_session_ids: list[SessionId] = []
        for session_id in dict.fromkeys(session_ids):
            allocated_resource_names = resources_by_session.get(session_id)
            if allocated_resource_names is None:
                continue
            if resource_name not in allocated_resource_names:
                continue
            applicable_session_ids.append(session_id)
        return applicable_session_ids

    async def query_session_utilization(
        self,
        action: SessionUtilizationAction,
    ) -> SessionUtilizationActionResult:
        session_ids = list(dict.fromkeys(action.session_ids))
        if not session_ids:
            return SessionUtilizationActionResult(observations_by_session={})

        allocations = await self._session_repository.batch_get_resource_allocation_by_session(
            session_ids
        )
        resources_by_session: dict[SessionId, set[str]] = {}
        for session_id, allocation in allocations.items():
            resource_names: set[str] = set()
            for slot_name, quantity in allocation.used.items():
                if Decimal(quantity) <= 0:
                    continue
                resource_names.add(str(slot_name).partition(".")[0])
            resources_by_session[session_id] = resource_names

        observations_by_session: defaultdict[SessionId, list[SessionUtilizationObservation]] = (
            defaultdict(list)
        )
        unknown_session_ids: set[SessionId] = set()
        for threshold in action.thresholds:
            applicable_session_ids = self._get_applicable_session_ids(
                threshold,
                session_ids,
                resources_by_session,
            )
            if not applicable_session_ids:
                continue
            # Sessions without metric values remain unknown.
            result = await self._metric_repository.query_session_utilization_metrics(
                SessionUtilizationMetricQuery(
                    metric_name=threshold.metric_name,
                    kernel_aggregation=threshold.kernel_aggregation,
                    time_window_seconds=threshold.time_window_seconds,
                    session_ids=applicable_session_ids,
                    evaluation_time=action.evaluation_time,
                )
            )
            for session_id in applicable_session_ids:
                value = result.by_session.get(session_id)
                if value is None:
                    unknown_session_ids.add(session_id)
                    continue
                value = self._to_utilization_percentage(
                    threshold.metric_name,
                    value,
                    allocations[session_id],
                )
                if value is None:
                    unknown_session_ids.add(session_id)
                    continue
                observations_by_session[session_id].append(
                    SessionUtilizationObservation(entry=threshold, value=value)
                )

        for session_id in unknown_session_ids:
            observations_by_session.pop(session_id, None)
        return SessionUtilizationActionResult(observations_by_session=dict(observations_by_session))

    async def query_container_metric_metadata(
        self,
        _action: ContainerMetricMetadataAction,
    ) -> ContainerMetricMetadataActionResult:
        metric_names = await self._metric_repository.query_container_metric_metadata()
        return ContainerMetricMetadataActionResult(metric_names=metric_names)

    async def query_container_metric(
        self,
        action: ContainerMetricAction,
    ) -> ContainerMetricActionResult:
        result = await self._metric_repository.query_container_metric(
            action.metric_name,
            action.labels,
            action.time_range,
        )
        return ContainerMetricActionResult(result=result)

    async def query_container_live_stats(
        self,
        action: ContainerLiveStatAction,
    ) -> ContainerLiveStatActionResult:
        stats = await self._metric_repository.query_container_live_stats(action.kernel_ids)
        return ContainerLiveStatActionResult(stats=stats)
