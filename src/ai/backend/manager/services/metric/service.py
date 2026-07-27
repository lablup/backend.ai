import logging
from collections import defaultdict
from decimal import Decimal

from ai.backend.common.data.idle_checker.types import (
    UtilizationKernelPolicy,
    UtilizationThresholdEntry,
)
from ai.backend.common.types import SessionId
from ai.backend.logging import BraceStyleAdapter
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
    SessionUtilizationBatchAction,
    SessionUtilizationBatchActionResult,
    SessionUtilizationObservation,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

_RESOURCE_METRIC_SUFFIXES = ("_util", "_mem", "_used")

type _QueryKey = tuple[str, UtilizationKernelPolicy, int | None]
type _ObservationTarget = tuple[int, SessionId, UtilizationThresholdEntry]


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

    async def query_session_utilization_batch(
        self,
        action: SessionUtilizationBatchAction,
    ) -> SessionUtilizationBatchActionResult:
        session_ids = {session_id for check in action.checks for session_id in check.session_ids}
        if not session_ids:
            return SessionUtilizationBatchActionResult(
                observations_by_check=[{} for _ in action.checks]
            )

        allocations = await self._session_repository.batch_get_resource_allocation_by_session(
            list(session_ids)
        )
        resources_by_session: dict[SessionId, set[str]] = {}
        for session_id, allocation in allocations.items():
            resource_names: set[str] = set()
            for slot_name, quantity in allocation.used.items():
                if Decimal(quantity) <= 0:
                    continue
                resource_names.add(str(slot_name).partition(".")[0])
            resources_by_session[session_id] = resource_names

        targets_by_query: defaultdict[_QueryKey, list[_ObservationTarget]] = defaultdict(list)
        # Filter sessions without resource allocations for each metric.
        for check_index, check in enumerate(action.checks):
            for entry in check.spec.thresholds:
                resource_name = entry.metric_name
                for suffix in _RESOURCE_METRIC_SUFFIXES:
                    if resource_name.endswith(suffix):
                        resource_name = resource_name.removesuffix(suffix)
                        break
                query_key = (
                    entry.metric_name,
                    entry.kernel_policy,
                    entry.time_window_seconds,
                )
                for session_id in check.session_ids:
                    allocated_resource_names = resources_by_session.get(session_id)
                    if allocated_resource_names is None:
                        continue
                    if resource_name not in allocated_resource_names:
                        continue
                    targets_by_query[query_key].append((check_index, session_id, entry))

        observations_by_check: list[defaultdict[SessionId, list[SessionUtilizationObservation]]] = [
            defaultdict(list) for _ in action.checks
        ]
        unknown_sessions: set[tuple[int, SessionId]] = set()
        for query_key, targets in targets_by_query.items():
            metric_name, kernel_policy, time_window_seconds = query_key
            query_session_ids = list(dict.fromkeys(session_id for _, session_id, _ in targets))
            # Sessions without metric values remain unknown.
            result = await self._metric_repository.query_session_utilization_metrics(
                SessionUtilizationMetricQuery(
                    metric_name=metric_name,
                    kernel_policy=kernel_policy,
                    time_window_seconds=time_window_seconds,
                    session_ids=query_session_ids,
                    evaluation_time=action.evaluation_time,
                )
            )
            for check_index, session_id, entry in targets:
                value = result.by_session.get(session_id)
                if value is None:
                    unknown_sessions.add((check_index, session_id))
                    continue
                value = self._to_utilization_percentage(
                    entry.metric_name,
                    value,
                    allocations[session_id],
                )
                if value is None:
                    unknown_sessions.add((check_index, session_id))
                    continue
                observations_by_check[check_index][session_id].append(
                    SessionUtilizationObservation(entry=entry, value=value)
                )

        for check_index, session_id in unknown_sessions:
            observations_by_check[check_index].pop(session_id, None)
        return SessionUtilizationBatchActionResult(
            observations_by_check=[
                dict(observations_by_session) for observations_by_session in observations_by_check
            ]
        )

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
