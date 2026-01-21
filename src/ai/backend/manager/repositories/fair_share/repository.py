"""Fair Share Repository with Resilience policies."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import date
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
from ai.backend.manager.data.fair_share import (
    DomainFairShareData,
    DomainFairShareSearchResult,
    ProjectFairShareData,
    ProjectFairShareSearchResult,
    ProjectUserIds,
    UserFairShareData,
    UserFairShareFactors,
    UserFairShareSearchResult,
)
from ai.backend.manager.repositories.base import BatchQuerier, Creator, Upserter

from .db_source import FairShareDBSource

if TYPE_CHECKING:
    from ai.backend.manager.models.fair_share import (
        DomainFairShareRow,
        ProjectFairShareRow,
        UserFairShareRow,
    )
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
    from ai.backend.manager.sokovan.scheduler.fair_share import FairShareFactorCalculationResult


__all__ = ("FairShareRepository",)


fair_share_repository_resilience = Resilience(
    policies=[
        MetricPolicy(
            MetricArgs(domain=DomainType.REPOSITORY, layer=LayerType.FAIR_SHARE_REPOSITORY)
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


class FairShareRepository:
    """Repository for Fair Share data access with resilience policies."""

    _db_source: FairShareDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = FairShareDBSource(db)

    # ==================== Domain Fair Share ====================

    @fair_share_repository_resilience.apply()
    async def create_domain_fair_share(
        self,
        creator: Creator[DomainFairShareRow],
    ) -> DomainFairShareData:
        """Create a new domain fair share record."""
        return await self._db_source.create_domain_fair_share(creator)

    @fair_share_repository_resilience.apply()
    async def upsert_domain_fair_share(
        self,
        upserter: Upserter[DomainFairShareRow],
    ) -> DomainFairShareData:
        """Upsert a domain fair share record."""
        return await self._db_source.upsert_domain_fair_share(upserter)

    @fair_share_repository_resilience.apply()
    async def get_domain_fair_share(
        self,
        resource_group: str,
        domain_name: str,
    ) -> DomainFairShareData:
        """Get a domain fair share record by scaling group and domain name.

        Raises:
            FairShareNotFoundError: If the domain fair share is not found.
        """
        return await self._db_source.get_domain_fair_share(resource_group, domain_name)

    @fair_share_repository_resilience.apply()
    async def search_domain_fair_shares(
        self,
        querier: BatchQuerier,
    ) -> DomainFairShareSearchResult:
        """Search domain fair shares with pagination."""
        return await self._db_source.search_domain_fair_shares(querier)

    # ==================== Project Fair Share ====================

    @fair_share_repository_resilience.apply()
    async def create_project_fair_share(
        self,
        creator: Creator[ProjectFairShareRow],
    ) -> ProjectFairShareData:
        """Create a new project fair share record."""
        return await self._db_source.create_project_fair_share(creator)

    @fair_share_repository_resilience.apply()
    async def upsert_project_fair_share(
        self,
        upserter: Upserter[ProjectFairShareRow],
    ) -> ProjectFairShareData:
        """Upsert a project fair share record."""
        return await self._db_source.upsert_project_fair_share(upserter)

    @fair_share_repository_resilience.apply()
    async def get_project_fair_share(
        self,
        resource_group: str,
        project_id: uuid.UUID,
    ) -> ProjectFairShareData:
        """Get a project fair share record by scaling group and project ID.

        Raises:
            FairShareNotFoundError: If the project fair share is not found.
        """
        return await self._db_source.get_project_fair_share(resource_group, project_id)

    @fair_share_repository_resilience.apply()
    async def search_project_fair_shares(
        self,
        querier: BatchQuerier,
    ) -> ProjectFairShareSearchResult:
        """Search project fair shares with pagination."""
        return await self._db_source.search_project_fair_shares(querier)

    # ==================== User Fair Share ====================

    @fair_share_repository_resilience.apply()
    async def create_user_fair_share(
        self,
        creator: Creator[UserFairShareRow],
    ) -> UserFairShareData:
        """Create a new user fair share record."""
        return await self._db_source.create_user_fair_share(creator)

    @fair_share_repository_resilience.apply()
    async def upsert_user_fair_share(
        self,
        upserter: Upserter[UserFairShareRow],
    ) -> UserFairShareData:
        """Upsert a user fair share record."""
        return await self._db_source.upsert_user_fair_share(upserter)

    @fair_share_repository_resilience.apply()
    async def get_user_fair_share(
        self,
        resource_group: str,
        project_id: uuid.UUID,
        user_uuid: uuid.UUID,
    ) -> UserFairShareData:
        """Get a user fair share record by scaling group, project ID, and user UUID.

        Raises:
            FairShareNotFoundError: If the user fair share is not found.
        """
        return await self._db_source.get_user_fair_share(resource_group, project_id, user_uuid)

    @fair_share_repository_resilience.apply()
    async def search_user_fair_shares(
        self,
        querier: BatchQuerier,
    ) -> UserFairShareSearchResult:
        """Search user fair shares with pagination."""
        return await self._db_source.search_user_fair_shares(querier)

    @fair_share_repository_resilience.apply()
    async def get_user_scheduling_ranks_batch(
        self,
        resource_group: str,
        project_user_ids: Sequence[ProjectUserIds],
    ) -> dict[uuid.UUID, int]:
        """Get scheduling ranks for multiple users across projects.

        Args:
            resource_group: The resource group (scaling group) name.
            project_user_ids: Sequence of ProjectUserIds containing project and user IDs.

        Returns:
            A mapping from user_uuid to scheduling_rank.
            Users not found in the database or with NULL rank are omitted.
        """
        return await self._db_source.get_user_scheduling_ranks_batch(
            resource_group, project_user_ids
        )

    # ==================== Bulk Factor Updates ====================

    @fair_share_repository_resilience.apply()
    async def bulk_update_fair_share_factors(
        self,
        resource_group: str,
        calculation_result: FairShareFactorCalculationResult,
        lookback_start: date,
        lookback_end: date,
    ) -> None:
        """Bulk update fair share factors for all levels.

        Updates domain, project, and user fair share records with calculated
        factors in a single transaction.

        Args:
            resource_group: The resource group being updated
            calculation_result: Calculated factors from FairShareFactorCalculator
            lookback_start: Start of lookback period used in calculation
            lookback_end: End of lookback period used in calculation
        """
        return await self._db_source.bulk_update_fair_share_factors(
            resource_group, calculation_result, lookback_start, lookback_end
        )

    @fair_share_repository_resilience.apply()
    async def get_all_fair_shares_for_resource_group(
        self,
        resource_group: str,
    ) -> tuple[
        dict[str, DomainFairShareData],
        dict[uuid.UUID, ProjectFairShareData],
        dict[tuple[uuid.UUID, uuid.UUID], UserFairShareData],
    ]:
        """Get all fair share records for a resource group.

        Used for factor calculation to get current weights and configurations.

        Args:
            resource_group: The resource group to query

        Returns:
            Tuple of (domain_fair_shares, project_fair_shares, user_fair_shares)
        """
        return await self._db_source.get_all_fair_shares_for_resource_group(resource_group)

    @fair_share_repository_resilience.apply()
    async def get_user_fair_share_factors_batch(
        self,
        resource_group: str,
        project_user_ids: Sequence[ProjectUserIds],
    ) -> dict[uuid.UUID, UserFairShareFactors]:
        """Get combined fair share factors for multiple users with 3-way JOIN.

        Fetches domain, project, and user fair share factors in a single query
        by joining the three fair share tables. Used for factor-based workload
        sequencing in FairShareSequencer.

        Args:
            resource_group: The resource group (scaling group) name.
            project_user_ids: Sequence of ProjectUserIds containing project and user IDs.

        Returns:
            A mapping from user_uuid to UserFairShareFactors containing all three factor levels.
            Users not found in any of the fair share tables are omitted.
        """
        return await self._db_source.get_user_fair_share_factors_batch(
            resource_group, project_user_ids
        )
