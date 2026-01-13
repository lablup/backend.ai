"""Database source for group configuration operations."""

from __future__ import annotations

import uuid
from typing import Optional

import sqlalchemy as sa

from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.manager.errors.resource import ProjectNotFound
from ai.backend.manager.models.group import (
    GroupDotfile,
    association_groups_users,
    groups,
    query_group_domain,
    query_group_dotfiles,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


class GroupConfigDBSource:
    """Database source for group configuration operations."""

    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def resolve_group_id_and_domain(
        self, group_id_or_name: uuid.UUID | str, domain_name: Optional[str]
    ) -> tuple[uuid.UUID, str]:
        """
        Resolve group ID and domain from group ID or name.

        Returns:
            Tuple of (group_id, domain_name)

        Raises:
            InvalidAPIParameters: If domain_name is missing when group name is provided
            ProjectNotFound: If group is not found
        """
        async with self._db.begin_readonly_session() as session:
            if isinstance(group_id_or_name, str):
                if domain_name is None:
                    raise InvalidAPIParameters("Missing parameter 'domain'")
                query = (
                    sa.select(groups.c.id)
                    .select_from(groups)
                    .where(groups.c.domain_name == domain_name)
                    .where(groups.c.name == group_id_or_name)
                )
                group_id = await session.scalar(query)
                if group_id is None:
                    raise ProjectNotFound()
                return group_id, domain_name

            group_id = group_id_or_name
            conn = await session.connection()
            domain = await query_group_domain(conn, group_id)  # type: ignore[arg-type]
            if domain is None:
                raise ProjectNotFound()
            return group_id, domain

    async def get_dotfiles(self, group_id: uuid.UUID) -> tuple[list[GroupDotfile], int]:
        """
        Get dotfiles for a group.

        Returns:
            Tuple of (dotfiles list, leftover space)

        Raises:
            ProjectNotFound: If group is not found
        """
        async with self._db.begin_readonly_session() as session:
            conn = await session.connection()
            dotfiles, leftover_space = await query_group_dotfiles(conn, group_id)  # type: ignore[arg-type]
            if dotfiles is None:
                raise ProjectNotFound()
            return dotfiles, leftover_space

    async def update_dotfiles(self, group_id: uuid.UUID, dotfiles_packed: bytes) -> None:
        """Update dotfiles for a group."""
        async with self._db.begin_session() as session:
            query = groups.update().values(dotfiles=dotfiles_packed).where(groups.c.id == group_id)
            await session.execute(query)

    async def check_user_in_group(self, user_id: uuid.UUID, group_id: uuid.UUID) -> bool:
        """Check if a user is a member of the group."""
        async with self._db.begin_readonly_session() as session:
            query = (
                sa.select(association_groups_users.c.group_id)
                .select_from(association_groups_users)
                .where(association_groups_users.c.user_id == user_id)
                .where(association_groups_users.c.group_id == group_id)
            )
            result = await session.scalar(query)
            return result is not None
