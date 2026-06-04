"""Repository for replica group operations."""

from __future__ import annotations

import logging
from collections.abc import Sequence

from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.deployment.types import ReplicaGroupHandlerCategory
from ai.backend.manager.models.replica_group import ReplicaGroupRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.base.updater import BulkUpdaterResult, Updater
from ai.backend.manager.repositories.replica_group.types import (
    LifecycleReconcileFetch,
    ReplicaGroupLifecycleReconcileApply,
    ReplicaGroupScalingReconcileApply,
    ScalingReconcileFetch,
)
from ai.backend.manager.views.replica_group import (
    ReplicaGroupDeploySchedulingView,
    ReplicaGroupScalingSchedulingView,
)

from .db_source import ReplicaGroupDBSource

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


replica_group_repository_resilience = Resilience(
    policies=[
        MetricPolicy(
            MetricArgs(domain=DomainType.REPOSITORY, layer=LayerType.REPLICA_GROUP_REPOSITORY)
        ),
        RetryPolicy(
            RetryArgs(
                max_retries=3,
                retry_delay=0.1,
                backoff_strategy=BackoffStrategy.FIXED,
                non_retryable_exceptions=(BackendAIError,),
            )
        ),
    ]
)


class ReplicaGroupRepository:
    """Repository for replica group reconcile operations."""

    _db_source: ReplicaGroupDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = ReplicaGroupDBSource(db)

    @replica_group_repository_resilience.apply()
    async def search_deploy_scheduling_views(
        self,
        querier: BatchQuerier,
    ) -> list[ReplicaGroupDeploySchedulingView]:
        return await self._db_source.search_deploy_scheduling_views(querier)

    @replica_group_repository_resilience.apply()
    async def search_scaling_scheduling_views(
        self,
        querier: BatchQuerier,
    ) -> list[ReplicaGroupScalingSchedulingView]:
        return await self._db_source.search_scaling_scheduling_views(querier)

    @replica_group_repository_resilience.apply()
    async def fetch_scaling_reconcile_views(
        self,
        querier: BatchQuerier,
        category: ReplicaGroupHandlerCategory,
    ) -> ScalingReconcileFetch:
        return await self._db_source.fetch_scaling_reconcile_views(querier, category)

    @replica_group_repository_resilience.apply()
    async def fetch_lifecycle_reconcile_views(
        self,
        querier: BatchQuerier,
        category: ReplicaGroupHandlerCategory,
    ) -> LifecycleReconcileFetch:
        return await self._db_source.fetch_lifecycle_reconcile_views(querier, category)

    @replica_group_repository_resilience.apply()
    async def update_replica_groups(
        self,
        updaters: Sequence[Updater[ReplicaGroupRow]],
    ) -> BulkUpdaterResult[ReplicaGroupRow]:
        return await self._db_source.update_replica_groups(updaters)

    @replica_group_repository_resilience.apply()
    async def apply_scaling_reconcile(
        self,
        apply: ReplicaGroupScalingReconcileApply,
    ) -> None:
        return await self._db_source.apply_scaling_reconcile(apply)

    @replica_group_repository_resilience.apply()
    async def apply_lifecycle_reconcile(
        self,
        apply: ReplicaGroupLifecycleReconcileApply,
    ) -> None:
        return await self._db_source.apply_lifecycle_reconcile(apply)
