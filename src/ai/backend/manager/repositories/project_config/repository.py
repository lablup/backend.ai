"""Repository for project configuration (dotfiles) operations."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Optional

from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.repositories.project_config.types import (
    DotfileInput,
    ProjectDotfilesResult,
    ResolvedProject,
)

from .db_source.db_source import ProjectConfigDBSource

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

project_config_repository_resilience = Resilience(
    policies=[
        # NOTE: GROUP_REPOSITORY is a metric layer enum value from the DB schema.
        MetricPolicy(MetricArgs(domain=DomainType.REPOSITORY, layer=LayerType.GROUP_REPOSITORY)),
        RetryPolicy(
            RetryArgs(
                max_retries=10,
                retry_delay=0.1,
                backoff_strategy=BackoffStrategy.FIXED,
            )
        ),
    ]
)


class ProjectConfigRepository:
    """Repository for project configuration (dotfiles) operations."""

    _db_source: ProjectConfigDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = ProjectConfigDBSource(db)

    @project_config_repository_resilience.apply()
    async def resolve_group(
        self, domain_name: Optional[str], group_id_or_name: uuid.UUID | str
    ) -> ResolvedProject:
        """
        Resolve project identity (id + domain_name) in a single query.

        Args:
            domain_name: Domain name (required if group_id_or_name is a string name)
            group_id_or_name: UUID or string name of the project

        Returns:
            ResolvedProject containing id and domain_name

        Raises:
            InvalidAPIParameters: If domain_name is missing when project name is provided
            ProjectNotFound: If project is not found
        """
        return await self._db_source.resolve_group(domain_name, group_id_or_name)

    @project_config_repository_resilience.apply()
    async def get_dotfiles(self, group_id: uuid.UUID) -> ProjectDotfilesResult:
        """
        Get dotfiles for a project.

        Returns:
            ProjectDotfilesResult containing dotfiles list and leftover space

        Raises:
            ProjectNotFound: If project is not found
        """
        return await self._db_source.get_dotfiles(group_id)

    @project_config_repository_resilience.apply()
    async def check_user_in_group(self, user_id: uuid.UUID, group_id: uuid.UUID) -> bool:
        """Check if a user is a member of the project."""
        return await self._db_source.check_user_in_group(user_id, group_id)

    @project_config_repository_resilience.apply()
    async def add_dotfile(self, group_id: uuid.UUID, dotfile: DotfileInput) -> None:
        """
        Add a new dotfile to the project.

        Raises:
            ProjectNotFound: If project is not found
            DotfileAlreadyExists: If dotfile with same path already exists
            DotfileCreationFailed: If no space left or limit reached
        """
        await self._db_source.add_dotfile(group_id, dotfile)

    @project_config_repository_resilience.apply()
    async def modify_dotfile(self, group_id: uuid.UUID, dotfile: DotfileInput) -> None:
        """
        Update an existing dotfile in the project.

        Raises:
            ProjectNotFound: If project is not found
            DotfileNotFound: If dotfile with the path does not exist
            DotfileCreationFailed: If updated content exceeds size limit
        """
        await self._db_source.modify_dotfile(group_id, dotfile)

    @project_config_repository_resilience.apply()
    async def remove_dotfile(self, group_id: uuid.UUID, path: str) -> None:
        """
        Remove a dotfile from the project.

        Raises:
            ProjectNotFound: If project is not found
            DotfileNotFound: If dotfile with the path does not exist
        """
        await self._db_source.remove_dotfile(group_id, path)
