"""DataLoader functions for deployment-related entities."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from typing import Optional

from ai.backend.manager.data.deployment.types import (
    ModelDeploymentData,
    ModelReplicaData,
    ModelRevisionData,
    RouteInfo,
)
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.deployment.options import (
    DeploymentConditions,
    RevisionConditions,
    RouteConditions,
)
from ai.backend.manager.services.deployment.actions.model_revision.search_revisions import (
    SearchRevisionsAction,
)
from ai.backend.manager.services.deployment.actions.route import SearchRoutesAction
from ai.backend.manager.services.deployment.actions.search_deployments import (
    SearchDeploymentsAction,
)
from ai.backend.manager.services.deployment.actions.search_replicas import (
    SearchReplicasAction,
)
from ai.backend.manager.services.deployment.processors import DeploymentProcessors


async def load_routes_by_ids(
    processor: DeploymentProcessors,
    route_ids: Sequence[uuid.UUID],
) -> list[Optional[RouteInfo]]:
    """Batch load routes by their IDs.

    Args:
        processor: The deployment processor.
        route_ids: Sequence of route UUIDs to load.

    Returns:
        List of RouteInfo (or None if not found) in the same order as route_ids.
    """
    if not route_ids:
        return []

    querier = BatchQuerier(
        pagination=OffsetPagination(limit=len(route_ids)),
        conditions=[RouteConditions.by_ids(route_ids)],
    )

    action_result = await processor.search_routes.wait_for_complete(
        SearchRoutesAction(querier=querier)
    )

    route_map = {route.route_id: route for route in action_result.routes}
    return [route_map.get(route_id) for route_id in route_ids]


async def load_deployments_by_ids(
    processor: DeploymentProcessors,
    deployment_ids: Sequence[uuid.UUID],
) -> list[Optional[ModelDeploymentData]]:
    """Batch load deployments by their IDs.

    Args:
        processor: The deployment processor.
        deployment_ids: Sequence of deployment UUIDs to load.

    Returns:
        List of ModelDeploymentData (or None if not found) in the same order as deployment_ids.
    """
    if not deployment_ids:
        return []

    querier = BatchQuerier(
        pagination=OffsetPagination(limit=len(deployment_ids)),
        conditions=[DeploymentConditions.by_ids(deployment_ids)],
    )

    action_result = await processor.search_deployments.wait_for_complete(
        SearchDeploymentsAction(querier=querier)
    )

    deployment_map = {deployment.id: deployment for deployment in action_result.data}
    return [deployment_map.get(deployment_id) for deployment_id in deployment_ids]


async def load_revisions_by_ids(
    processor: DeploymentProcessors,
    revision_ids: Sequence[uuid.UUID],
) -> list[Optional[ModelRevisionData]]:
    """Batch load revisions by their IDs.

    Args:
        processor: The deployment processor.
        revision_ids: Sequence of revision UUIDs to load.

    Returns:
        List of ModelRevisionData (or None if not found) in the same order as revision_ids.
    """
    if not revision_ids:
        return []

    querier = BatchQuerier(
        pagination=OffsetPagination(limit=len(revision_ids)),
        conditions=[RevisionConditions.by_ids(revision_ids)],
    )

    action_result = await processor.search_revisions.wait_for_complete(
        SearchRevisionsAction(querier=querier)
    )

    revision_map = {revision.id: revision for revision in action_result.data}
    return [revision_map.get(revision_id) for revision_id in revision_ids]


async def load_replicas_by_ids(
    processor: DeploymentProcessors,
    replica_ids: Sequence[uuid.UUID],
) -> list[Optional[ModelReplicaData]]:
    """Batch load replicas by their IDs.

    Args:
        processor: The deployment processor.
        replica_ids: Sequence of replica UUIDs to load.

    Returns:
        List of ModelReplicaData (or None if not found) in the same order as replica_ids.
    """
    if not replica_ids:
        return []

    querier = BatchQuerier(
        pagination=OffsetPagination(limit=len(replica_ids)),
        conditions=[RouteConditions.by_ids(replica_ids)],
    )

    action_result = await processor.search_replicas.wait_for_complete(
        SearchReplicasAction(querier=querier)
    )

    replica_map = {replica.id: replica for replica in action_result.data}
    return [replica_map.get(replica_id) for replica_id in replica_ids]
