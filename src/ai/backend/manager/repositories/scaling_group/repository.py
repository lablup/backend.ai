from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

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
from ai.backend.manager.models.scaling_group import (
    ScalingGroupForDomainRow,
    ScalingGroupForKeypairsRow,
    ScalingGroupForProjectRow,
    ScalingGroupRow,
)
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.base.creator import BulkCreator, Creator
from ai.backend.manager.repositories.base.purger import BatchPurger, Purger
from ai.backend.manager.repositories.base.updater import Updater

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

    @scaling_group_repository_resilience.apply()
    async def update_scaling_group(
        self,
        updater: Updater[ScalingGroupRow],
    ) -> ScalingGroupData:
        """Updates an existing scaling group.

        Raises ScalingGroupNotFound if the scaling group does not exist.
        """
        return await self._db_source.update_scaling_group(updater)

    async def associate_scaling_group_with_domains(
        self,
        bulk_creator: BulkCreator[ScalingGroupForDomainRow],
    ) -> None:
        """Associates a scaling group with multiple domains."""
        await self._db_source.associate_scaling_group_with_domains(bulk_creator)

    async def disassociate_scaling_group_with_domains(
        self,
        purger: BatchPurger[ScalingGroupForDomainRow],
    ) -> None:
        """Disassociates a scaling group from multiple domains."""
        await self._db_source.disassociate_scaling_group_with_domains(purger)

    async def check_scaling_group_domain_association_exists(
        self,
        scaling_group: str,
        domain: str,
    ) -> bool:
        """Checks if a scaling group is associated with a domain."""
        return await self._db_source.check_scaling_group_domain_association_exists(
            scaling_group=scaling_group,
            domain=domain,
        )

    async def associate_scaling_group_with_keypairs(
        self,
        bulk_creator: BulkCreator[ScalingGroupForKeypairsRow],
    ) -> None:
        """Associates a scaling group with multiple keypairs."""
        await self._db_source.associate_scaling_group_with_keypairs(bulk_creator)

    async def disassociate_scaling_group_with_keypairs(
        self,
        purger: BatchPurger[ScalingGroupForKeypairsRow],
    ) -> None:
        """Disassociates a scaling group from multiple keypairs."""
        await self._db_source.disassociate_scaling_group_with_keypairs(purger)

    async def check_scaling_group_keypair_association_exists(
        self,
        scaling_group_name: str,
        access_key: str,
    ) -> bool:
        """Checks if a scaling group is associated with a keypair."""
        return await self._db_source.check_scaling_group_keypair_association_exists(
            scaling_group_name, access_key
        )

    async def associate_scaling_group_with_user_groups(
        self,
        bulk_creator: BulkCreator[ScalingGroupForProjectRow],
    ) -> None:
        """Associates a scaling group with multiple user groups (projects)."""
        await self._db_source.associate_scaling_group_with_user_groups(bulk_creator)

    async def disassociate_scaling_group_with_user_groups(
        self,
        purger: BatchPurger[ScalingGroupForProjectRow],
    ) -> None:
        """Disassociates a single scaling group from a user group (project)."""
        await self._db_source.disassociate_scaling_group_with_user_groups(purger)

    async def check_scaling_group_user_group_association_exists(
        self,
        scaling_group: str,
        user_group: UUID,
    ) -> bool:
        """Checks if a scaling group is associated with a user group (project)."""
        return await self._db_source.check_scaling_group_user_group_association_exists(
            scaling_group=scaling_group,
            user_group=user_group,
        )
