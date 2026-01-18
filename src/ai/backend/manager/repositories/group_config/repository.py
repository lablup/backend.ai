"""Repository for group configuration (dotfiles) operations."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Optional

from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.models.group import GroupDotfile

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
    async def resolve_group_id_and_domain(
        self, group_id_or_name: uuid.UUID | str, domain_name: Optional[str]
    ) -> tuple[uuid.UUID, str]:
        """
        Resolve group ID and domain from group ID or name.

        Args:
            group_id_or_name: UUID or string name of the group
            domain_name: Domain name (required if group_id_or_name is a string name)

        Returns:
            Tuple of (group_id, domain_name)

        Raises:
            InvalidAPIParameters: If domain_name is missing when group name is provided
            ProjectNotFound: If group is not found
        """
        return await self._db_source.resolve_group_id_and_domain(group_id_or_name, domain_name)

    @group_config_repository_resilience.apply()
    async def get_dotfiles(self, group_id: uuid.UUID) -> tuple[list[GroupDotfile], int]:
        """
        Get dotfiles for a group.

        Returns:
            Tuple of (dotfiles list, leftover space)

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
