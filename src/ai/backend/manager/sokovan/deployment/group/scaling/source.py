"""Source that assembles the group scaling reconcile info in one fetch."""

from __future__ import annotations

from typing import override

from ai.backend.manager.data.deployment.types import ReplicaGroupHandlerCategory
from ai.backend.manager.models.replica_group.conditions import ReplicaGroupConditions
from ai.backend.manager.repositories.base import BatchQuerier, NoPagination
from ai.backend.manager.repositories.replica_group.repository import ReplicaGroupRepository
from ai.backend.manager.sokovan.deployment.group.scaling.types import (
    GroupScalingReconcileInfo,
    GroupScalingTargetStatuses,
)
from ai.backend.manager.sokovan.reconciler.base import ReconcilerSource


class GroupScalingSource(
    ReconcilerSource[
        GroupScalingReconcileInfo,
        ReplicaGroupHandlerCategory,
        GroupScalingTargetStatuses,
    ]
):
    _replica_group_repository: ReplicaGroupRepository

    def __init__(self, replica_group_repository: ReplicaGroupRepository) -> None:
        self._replica_group_repository = replica_group_repository

    @override
    async def fetch_reconcile_info(
        self,
        category: ReplicaGroupHandlerCategory,
        target_statuses: GroupScalingTargetStatuses,
    ) -> GroupScalingReconcileInfo:
        querier = BatchQuerier(
            pagination=NoPagination(),
            conditions=[
                ReplicaGroupConditions.by_scaling_statuses(target_statuses.scaling_statuses),
            ],
        )
        fetch = await self._replica_group_repository.fetch_scaling_reconcile_views(
            querier, category
        )
        return GroupScalingReconcileInfo(views=fetch.views, current_time=fetch.now)
