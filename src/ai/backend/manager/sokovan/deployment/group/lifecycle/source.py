"""Source that assembles the group lifecycle reconcile info in one fetch."""

from __future__ import annotations

from ai.backend.manager.data.deployment.types import ReplicaGroupHandlerCategory
from ai.backend.manager.models.replica_group.conditions import ReplicaGroupConditions
from ai.backend.manager.repositories.base import BatchQuerier, NoPagination
from ai.backend.manager.repositories.replica_group.repository import ReplicaGroupRepository
from ai.backend.manager.sokovan.deployment.group.lifecycle.types import (
    GroupAutoscaleReconcileInfo,
    GroupLifecycleReconcileInfo,
    GroupLifecycleTargetStatuses,
)
from ai.backend.manager.sokovan.reconciler.base import ReconcilerSource


class GroupLifecycleSource(
    ReconcilerSource[
        GroupLifecycleReconcileInfo,
        ReplicaGroupHandlerCategory,
        GroupLifecycleTargetStatuses,
    ]
):
    _replica_group_repository: ReplicaGroupRepository

    def __init__(self, replica_group_repository: ReplicaGroupRepository) -> None:
        self._replica_group_repository = replica_group_repository

    async def fetch_reconcile_info(
        self,
        category: ReplicaGroupHandlerCategory,
        target_statuses: GroupLifecycleTargetStatuses,
    ) -> GroupLifecycleReconcileInfo:
        querier = BatchQuerier(
            pagination=NoPagination(),
            conditions=[
                ReplicaGroupConditions.by_lifecycles(target_statuses.lifecycles),
                ReplicaGroupConditions.by_scaling_statuses(target_statuses.scaling_statuses),
            ],
        )
        fetch = await self._replica_group_repository.fetch_lifecycle_reconcile_views(
            querier, category
        )
        return GroupLifecycleReconcileInfo(views=fetch.views, current_time=fetch.now)


class GroupAutoscaleSource(
    ReconcilerSource[
        GroupAutoscaleReconcileInfo,
        ReplicaGroupHandlerCategory,
        GroupLifecycleTargetStatuses,
    ]
):
    """Like the lifecycle source, but also fetches actual live/serving counts so the
    autoscale handler can detect drift between desired and reality."""

    _replica_group_repository: ReplicaGroupRepository

    def __init__(self, replica_group_repository: ReplicaGroupRepository) -> None:
        self._replica_group_repository = replica_group_repository

    async def fetch_reconcile_info(
        self,
        category: ReplicaGroupHandlerCategory,
        target_statuses: GroupLifecycleTargetStatuses,
    ) -> GroupAutoscaleReconcileInfo:
        querier = BatchQuerier(
            pagination=NoPagination(),
            conditions=[
                ReplicaGroupConditions.by_lifecycles(target_statuses.lifecycles),
                ReplicaGroupConditions.by_scaling_statuses(target_statuses.scaling_statuses),
            ],
        )
        fetch = await self._replica_group_repository.fetch_autoscale_reconcile_views(
            querier, category
        )
        return GroupAutoscaleReconcileInfo(views=fetch.views, current_time=fetch.now)
