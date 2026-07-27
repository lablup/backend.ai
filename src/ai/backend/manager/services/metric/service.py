import logging
from collections import defaultdict
from uuid import UUID

from ai.backend.common.types import SessionId
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.repositories.metric.repository import MetricRepository
from ai.backend.manager.repositories.metric.types import SessionUtilizationMetricQuery

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


class MetricService:
    _metric_repository: MetricRepository

    def __init__(
        self,
        metric_repository: MetricRepository,
    ) -> None:
        self._metric_repository = metric_repository

    async def query_session_utilization(
        self,
        action: SessionUtilizationAction,
    ) -> SessionUtilizationActionResult:
        session_ids_by_preset: defaultdict[UUID, dict[SessionId, None]] = defaultdict(dict)
        for query in action.queries:
            for session_id in query.session_ids:
                session_ids_by_preset[query.preset_id][session_id] = None

        observations_by_preset: dict[
            UUID,
            dict[SessionId, SessionUtilizationObservation],
        ] = {}
        for preset_id, session_ids in session_ids_by_preset.items():
            result = await self._metric_repository.query_session_utilization_metrics(
                SessionUtilizationMetricQuery(
                    preset_id=preset_id,
                    session_ids=list(session_ids),
                    evaluation_time=action.evaluation_time,
                )
            )
            observations_by_preset[preset_id] = {
                session_id: SessionUtilizationObservation(
                    preset_id=preset_id,
                    value=value,
                )
                for session_id, value in result.by_session.items()
            }
        return SessionUtilizationActionResult(observations_by_preset=observations_by_preset)

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
