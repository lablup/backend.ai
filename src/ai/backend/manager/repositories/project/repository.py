from __future__ import annotations

import logging
import uuid
from collections.abc import Sequence
from datetime import datetime
from typing import Any
from uuid import UUID

from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.common.types import ResourceSlot
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.errors.resource import (
    ProjectNotFound,
)
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.project.updaters import ProjectDotfilesUpdater, ProjectUpdater
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.project.db_source import ProjectDBSource

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


project_repository_resilience = Resilience(
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


class ProjectRepository:
    _db_source: ProjectDBSource
    _config_provider: ManagerConfigProvider
    _valkey_stat_client: ValkeyStatClient
    _storage_manager: StorageSessionManager

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
        v2_ops_provider: V2DBOpsProvider,
        config_provider: ManagerConfigProvider,
        valkey_stat_client: ValkeyStatClient,
        storage_manager: StorageSessionManager,
    ) -> None:
        self._db_source = ProjectDBSource(db, v2_ops_provider)
        self._v2_ops = v2_ops_provider
        self._config_provider = config_provider
        self._valkey_stat_client = valkey_stat_client
        self._storage_manager = storage_manager

    @project_repository_resilience.apply()
    async def modify_validated(
        self,
        updater: ProjectUpdater,
    ) -> ProjectData | None:
        """Modify a project. Who belongs to it is the roster's own operation."""
        async with self._v2_ops.write_ops() as w:
            return await w.update_data(updater)

    @project_repository_resilience.apply()
    async def update_dotfiles(self, updater: ProjectDotfilesUpdater) -> ProjectData:
        """Replace a project's packed dotfile entries."""
        async with self._v2_ops.write_ops() as w:
            data = await w.update_data(updater)
            if data is None:
                raise ProjectNotFound(f"Project not found: {updater.target_id_value()}")
            return data

    @project_repository_resilience.apply()
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

    @project_repository_resilience.apply()
    async def fetch_project_resource_usage(
        self,
        start_date: datetime,
        end_date: datetime,
        project_ids: Sequence[UUID] | None = None,
    ) -> tuple[list[KernelRow], dict[UUID, ResourceSlot]]:
        """Fetch the project's kernels with the slots they were allocated."""
        return await self._db_source.fetch_project_resource_usage(start_date, end_date, project_ids)

    @project_repository_resilience.apply()
    async def purge_group(self, group_id: uuid.UUID) -> bool:
        """Completely remove a group and all its associated data."""
        return await self._db_source.purge_group(group_id, self._storage_manager)

    @project_repository_resilience.apply()
    async def get_project(self, project_id: UUID) -> ProjectData:
        """Get a single project by UUID.

        Args:
            project_id: UUID of the project.

        Returns:
            ProjectData for the project.

        Raises:
            ProjectNotFound: If project does not exist.
        """
        return await self._db_source.get_project(project_id)

    @project_repository_resilience.apply()
    async def project_id_by_name_in_domain(
        self, domain_name: str, project_name: str
    ) -> ProjectID | None:
        """Resolve an active project's UUID by its domain-scoped name.

        LEGACY: Exists solely to support existing API handlers that only accept a
        group name as input (e.g. the REST v1 session/cluster template endpoints).
        New API handlers and any other new code MUST NOT use this — they should
        accept a project UUID directly.

        Returns:
            The project UUID if found, or ``None`` if no matching active project exists.
        """
        return await self._db_source.project_id_by_name_in_domain(domain_name, project_name)
