"""DataLoader functions for scheduling history entities."""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from ai.backend.manager.data.deployment.types import DeploymentHistoryData, RouteHistoryData
from ai.backend.manager.data.session.types import SessionSchedulingHistoryData
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.scheduling_history.options import (
    DeploymentHistoryConditions,
    RouteHistoryConditions,
    SessionSchedulingHistoryConditions,
)
from ai.backend.manager.services.scheduling_history.actions.search_deployment_history import (
    SearchDeploymentHistoryAction,
)
from ai.backend.manager.services.scheduling_history.actions.search_route_history import (
    SearchRouteHistoryAction,
)
from ai.backend.manager.services.scheduling_history.actions.search_session_history import (
    SearchSessionHistoryAction,
)
from ai.backend.manager.services.scheduling_history.processors import SchedulingHistoryProcessors


async def load_session_histories_by_ids(
    processor: SchedulingHistoryProcessors,
    history_ids: Sequence[uuid.UUID],
) -> list[SessionSchedulingHistoryData | None]:
    """Batch load session scheduling histories by their IDs."""
    if not history_ids:
        return []

    querier = BatchQuerier(
        pagination=OffsetPagination(limit=len(history_ids)),
        conditions=[SessionSchedulingHistoryConditions.by_ids(history_ids)],
    )

    action_result = await processor.search_session_history.wait_for_complete(
        SearchSessionHistoryAction(querier=querier)
    )

    history_map = {h.id: h for h in action_result.histories}
    return [history_map.get(history_id) for history_id in history_ids]


async def load_deployment_histories_by_ids(
    processor: SchedulingHistoryProcessors,
    history_ids: Sequence[uuid.UUID],
) -> list[DeploymentHistoryData | None]:
    """Batch load deployment histories by their IDs."""
    if not history_ids:
        return []

    querier = BatchQuerier(
        pagination=OffsetPagination(limit=len(history_ids)),
        conditions=[DeploymentHistoryConditions.by_ids(history_ids)],
    )

    action_result = await processor.search_deployment_history.wait_for_complete(
        SearchDeploymentHistoryAction(querier=querier)
    )

    history_map = {h.id: h for h in action_result.histories}
    return [history_map.get(history_id) for history_id in history_ids]


async def load_route_histories_by_ids(
    processor: SchedulingHistoryProcessors,
    history_ids: Sequence[uuid.UUID],
) -> list[RouteHistoryData | None]:
    """Batch load route histories by their IDs."""
    if not history_ids:
        return []

    querier = BatchQuerier(
        pagination=OffsetPagination(limit=len(history_ids)),
        conditions=[RouteHistoryConditions.by_ids(history_ids)],
    )

    action_result = await processor.search_route_history.wait_for_complete(
        SearchRouteHistoryAction(querier=querier)
    )

    history_map = {h.id: h for h in action_result.histories}
    return [history_map.get(history_id) for history_id in history_ids]
