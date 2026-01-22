"""Repository for group configuration (dotfiles) operations."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Optional

from ai.backend.common import msgpack
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.errors.storage import (
    DotfileAlreadyExists,
    DotfileCreationFailed,
    DotfileNotFound,
)
from ai.backend.manager.models.domain import MAXIMUM_DOTFILE_SIZE
from ai.backend.manager.repositories.group_config.types import DotfileInput, GroupDotfilesResult

from .db_source.db_source import GroupConfigDBSource

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

group_config_repository_resilience = Resilience(
    policies=[
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


class GroupConfigRepository:
    """Repository for group configuration (dotfiles) operations."""

    _db_source: GroupConfigDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = GroupConfigDBSource(db)

    @group_config_repository_resilience.apply()
    async def resolve_group_id(
        self, domain_name: Optional[str], group_id_or_name: uuid.UUID | str
    ) -> uuid.UUID:
        """
        Resolve group ID from group ID or name.

        Args:
            domain_name: Domain name (required if group_id_or_name is a string name)
            group_id_or_name: UUID or string name of the group

        Returns:
            group_id

        Raises:
            InvalidAPIParameters: If domain_name is missing when group name is provided
            ProjectNotFound: If group is not found
        """
        return await self._db_source.resolve_group_id(domain_name, group_id_or_name)

    @group_config_repository_resilience.apply()
    async def get_group_domain(self, group_id: uuid.UUID) -> str:
        """
        Get the domain name of a group.

        Args:
            group_id: UUID of the group

        Returns:
            domain_name

        Raises:
            ProjectNotFound: If group is not found
        """
        return await self._db_source.get_group_domain(group_id)

    @group_config_repository_resilience.apply()
    async def get_dotfiles(self, group_id: uuid.UUID) -> GroupDotfilesResult:
        """
        Get dotfiles for a group.

        Returns:
            GroupDotfilesResult containing dotfiles list and leftover space

        Raises:
            ProjectNotFound: If group is not found
        """
        return await self._db_source.get_dotfiles(group_id)

    @group_config_repository_resilience.apply()
    async def update_dotfiles(self, group_id: uuid.UUID, dotfiles_packed: bytes) -> None:
        """Update dotfiles for a group."""
        await self._db_source.update_dotfiles(group_id, dotfiles_packed)

    @group_config_repository_resilience.apply()
    async def check_user_in_group(self, user_id: uuid.UUID, group_id: uuid.UUID) -> bool:
        """Check if a user is a member of the group."""
        return await self._db_source.check_user_in_group(user_id, group_id)

    @group_config_repository_resilience.apply()
    async def add_dotfile(self, group_id: uuid.UUID, dotfile: DotfileInput) -> None:
        """
        Add a new dotfile to the group.

        Raises:
            ProjectNotFound: If group is not found
            DotfileAlreadyExists: If dotfile with same path already exists
            DotfileCreationFailed: If no space left or limit reached
        """
        result = await self._db_source.get_dotfiles(group_id)

        if result.leftover_space == 0:
            raise DotfileCreationFailed("No leftover space for dotfile storage")
        if len(result.dotfiles) >= 100:
            raise DotfileCreationFailed("Dotfile creation limit reached")

        duplicate = [x for x in result.dotfiles if x["path"] == dotfile.path]
        if len(duplicate) > 0:
            raise DotfileAlreadyExists

        new_dotfiles = list(result.dotfiles)
        new_dotfiles.append({
            "path": dotfile.path,
            "perm": dotfile.permission,
            "data": dotfile.data,
        })
        dotfile_packed = msgpack.packb(new_dotfiles)
        if len(dotfile_packed) > MAXIMUM_DOTFILE_SIZE:
            raise DotfileCreationFailed("No leftover space for dotfile storage")

        await self._db_source.update_dotfiles(group_id, dotfile_packed)

    @group_config_repository_resilience.apply()
    async def modify_dotfile(self, group_id: uuid.UUID, dotfile: DotfileInput) -> None:
        """
        Update an existing dotfile in the group.

        Raises:
            ProjectNotFound: If group is not found
            DotfileNotFound: If dotfile with the path does not exist
            DotfileCreationFailed: If updated content exceeds size limit
        """
        result = await self._db_source.get_dotfiles(group_id)

        new_dotfiles = [x for x in result.dotfiles if x["path"] != dotfile.path]
        if len(new_dotfiles) == len(result.dotfiles):
            raise DotfileNotFound

        new_dotfiles.append({
            "path": dotfile.path,
            "perm": dotfile.permission,
            "data": dotfile.data,
        })
        dotfile_packed = msgpack.packb(new_dotfiles)
        if len(dotfile_packed) > MAXIMUM_DOTFILE_SIZE:
            raise DotfileCreationFailed("No leftover space for dotfile storage")

        await self._db_source.update_dotfiles(group_id, dotfile_packed)

    @group_config_repository_resilience.apply()
    async def remove_dotfile(self, group_id: uuid.UUID, path: str) -> None:
        """
        Remove a dotfile from the group.

        Raises:
            ProjectNotFound: If group is not found
            DotfileNotFound: If dotfile with the path does not exist
        """
        result = await self._db_source.get_dotfiles(group_id)

        new_dotfiles = [x for x in result.dotfiles if x["path"] != path]
        if len(new_dotfiles) == len(result.dotfiles):
            raise DotfileNotFound

        dotfile_packed = msgpack.packb(new_dotfiles)
        await self._db_source.update_dotfiles(group_id, dotfile_packed)
