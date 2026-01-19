"""Fair Share Repository with Resilience policies."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from decimal import Decimal
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
    async def get_user_fair_share_factors_batch(
        self,
        resource_group: str,
        project_user_ids: Sequence[ProjectUserIds],
    ) -> dict[uuid.UUID, Decimal]:
        """Get fair share factors for multiple users across projects.

        Args:
            resource_group: The resource group (scaling group) name.
            project_user_ids: Sequence of ProjectUserIds containing project and user IDs.

        Returns:
            A mapping from user_uuid to fair_share_factor.
            Users not found in the database are omitted from the result.
        """
        return await self._db_source.get_user_fair_share_factors_batch(
            resource_group, project_user_ids
        )
