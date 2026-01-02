from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience import (
    MetricArgs,
    MetricPolicy,
    Resilience,
    RetryArgs,
    RetryPolicy,
)
from ai.backend.common.resilience.policies.retry import BackoffStrategy
from ai.backend.manager.data.scaling_group.types import ScalingGroupData, ScalingGroupListResult
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.purger import Purger

from .db_source import ScalingGroupDBSource

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

__all__ = ("ScalingGroupRepository",)


scaling_group_repository_resilience = Resilience(
    policies=[
        MetricPolicy(
            MetricArgs(domain=DomainType.REPOSITORY, layer=LayerType.SCALING_GROUP_REPOSITORY)
        ),
        RetryPolicy(
            RetryArgs(
                max_retries=10,
                retry_delay=0.1,
                backoff_strategy=BackoffStrategy.FIXED,
            )
        ),
    ]
)


class ScalingGroupRepository:
    """Repository for scaling group-related data access."""

    _db_source: ScalingGroupDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = ScalingGroupDBSource(db)

    @scaling_group_repository_resilience.apply()
    async def create_scaling_group(
        self,
        creator: Creator[ScalingGroupRow],
    ) -> ScalingGroupData:
        """Creates a new scaling group.

        Raises ScalingGroupConflict if a scaling group with the same name already exists.
        """
        return await self._db_source.create_scaling_group(creator)

    @scaling_group_repository_resilience.apply()
    async def search_scaling_groups(
        self,
        querier: BatchQuerier,
    ) -> ScalingGroupListResult:
        """Searches scaling groups with total count."""
        return await self._db_source.search_scaling_groups(querier=querier)

    @scaling_group_repository_resilience.apply()
    async def purge_scaling_group(
        self,
        purger: Purger[ScalingGroupRow],
    ) -> ScalingGroupData:
        """Purges a scaling group and all related sessions and routes using a purger.

        Raises ScalingGroupNotFound if scaling group doesn't exist.
        """
        return await self._db_source.purge_scaling_group(purger)
