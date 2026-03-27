from __future__ import annotations

import logging
import uuid
from collections.abc import Sequence
from datetime import datetime
from typing import Any
from uuid import UUID

from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.group.types import GroupData
from ai.backend.manager.errors.resource import InvalidUserUpdateMode
from ai.backend.manager.models.group.row import GroupRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.querier import BatchQuerier
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.group.db_source import GroupDBSource
from ai.backend.manager.repositories.group.types import (
    DomainProjectSearchScope,
    GroupSearchResult,
    UserProjectSearchScope,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


group_repository_resilience = Resilience(
    policies=[
        MetricPolicy(MetricArgs(domain=DomainType.REPOSITORY, layer=LayerType.GROUP_REPOSITORY)),
        RetryPolicy(
            RetryArgs(
                max_retries=10,
                retry_delay=0.1,
                backoff_strategy=BackoffStrategy.FIXED,
                non_retryable_exceptions=(BackendAIError,),
            )
        ),
    ]
)


class GroupRepository:
    _db_source: GroupDBSource
    _config_provider: ManagerConfigProvider
    _valkey_stat_client: ValkeyStatClient
    _storage_manager: StorageSessionManager

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
        config_provider: ManagerConfigProvider,
        valkey_stat_client: ValkeyStatClient,
        storage_manager: StorageSessionManager,
    ) -> None:
        self._db_source = GroupDBSource(db)
        self._config_provider = config_provider
        self._valkey_stat_client = valkey_stat_client
        self._storage_manager = storage_manager

    @group_repository_resilience.apply()
    async def create(self, creator: Creator[GroupRow]) -> GroupData:
        """Create a new group."""
        return await self._db_source.create(creator)

    @group_repository_resilience.apply()
    async def modify_validated(
        self,
        updater: Updater[GroupRow],
        user_update_mode: str | None = None,
        user_uuids: list[uuid.UUID] | None = None,
    ) -> GroupData | None:
        """Modify a group with validation."""
        if user_update_mode not in (None, "add", "remove"):
            raise InvalidUserUpdateMode("invalid user_update_mode")
        return await self._db_source.modify_validated(updater, user_update_mode, user_uuids)

    @group_repository_resilience.apply()
    async def mark_inactive(self, group_id: uuid.UUID) -> None:
        """Mark a group as inactive (soft delete)."""
        await self._db_source.mark_inactive(group_id)

    @group_repository_resilience.apply()
    async def get_container_stats_for_period(
        self,
        start_date: datetime,
        end_date: datetime,
        group_ids: Sequence[UUID] | None = None,
    ) -> list[dict[str, Any]]:
        """Get container statistics for groups within a time period."""
        return await self._db_source.get_container_stats_for_period(
            start_date,
            end_date,
            self._valkey_stat_client,
            self._config_provider,
            group_ids,
        )

    @group_repository_resilience.apply()
    async def fetch_project_resource_usage(
        self,
        start_date: datetime,
        end_date: datetime,
        project_ids: Sequence[UUID] | None = None,
    ) -> list[KernelRow]:
        """Fetch resource usage data for projects."""
        return await self._db_source.fetch_project_resource_usage(start_date, end_date, project_ids)

    @group_repository_resilience.apply()
    async def purge_group(self, group_id: uuid.UUID) -> bool:
        """Completely remove a group and all its associated data."""
        return await self._db_source.purge_group(group_id, self._storage_manager)

    @group_repository_resilience.apply()
    async def get_project(self, project_id: UUID) -> GroupData:
        """Get a single project by UUID.

        Args:
            project_id: UUID of the project.

        Returns:
            GroupData for the project.

        Raises:
            ProjectNotFound: If project does not exist.
        """
        return await self._db_source.get_project(project_id)

    @group_repository_resilience.apply()
    async def search_projects(
        self,
        querier: BatchQuerier,
    ) -> GroupSearchResult:
        """Search all projects (admin only).

        Args:
            querier: BatchQuerier containing conditions, orders, and pagination.

        Returns:
            GroupSearchResult with items, total_count, and pagination flags.
        """
        return await self._db_source.search_projects(querier)

    @group_repository_resilience.apply()
    async def search_projects_by_domain(
        self,
        scope: DomainProjectSearchScope,
        querier: BatchQuerier,
    ) -> GroupSearchResult:
        """Search projects within a domain.

        Args:
            scope: DomainProjectSearchScope defining the domain to search within.
            querier: BatchQuerier containing conditions, orders, and pagination.

        Returns:
            GroupSearchResult with items, total_count, and pagination flags.
        """
        return await self._db_source.search_projects_by_domain(scope, querier)

    @group_repository_resilience.apply()
    async def search_projects_by_user(
        self,
        scope: UserProjectSearchScope,
        querier: BatchQuerier,
    ) -> GroupSearchResult:
        """Search projects a user is member of.

        Args:
            scope: UserProjectSearchScope defining the user to search for.
            querier: BatchQuerier containing conditions, orders, and pagination.

        Returns:
            GroupSearchResult with items, total_count, and pagination flags.
        """
        return await self._db_source.search_projects_by_user(scope, querier)
