"""Database source for group configuration operations."""

from __future__ import annotations

import uuid
from typing import Optional

import sqlalchemy as sa

from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.manager.errors.resource import ProjectNotFound
from ai.backend.manager.models.group import (
    AssocGroupUserRow,
    GroupRow,
    query_group_dotfiles,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.group_config.types import GroupDotfilesResult, ResolvedGroup


class GroupConfigDBSource:
    """Database source for group configuration operations."""

    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def resolve_group(
        self, domain_name: Optional[str], group_id_or_name: uuid.UUID | str
    ) -> ResolvedGroup:
        """
        Resolve group identity (id + domain_name) in a single query.

        Args:
            domain_name: Domain name (required if group_id_or_name is a string name)
            group_id_or_name: UUID or string name of the group

        Returns:
            ResolvedGroup containing id and domain_name

        Raises:
            InvalidAPIParameters: If domain_name is missing when group name is provided
            ProjectNotFound: If group is not found
        """
        async with self._db.begin_readonly_session() as session:
            if isinstance(group_id_or_name, str):
                if domain_name is None:
                    raise InvalidAPIParameters("Missing parameter 'domain'")
                query = (
                    sa.select(GroupRow.id, GroupRow.domain_name)
                    .where(GroupRow.domain_name == domain_name)
                    .where(GroupRow.name == group_id_or_name)
                )
            else:
                query = sa.select(GroupRow.id, GroupRow.domain_name).where(
                    GroupRow.id == group_id_or_name
                )
            row = (await session.execute(query)).first()
            if row is None:
                raise ProjectNotFound()
            return ResolvedGroup(id=row.id, domain_name=row.domain_name)

    async def get_dotfiles(self, group_id: uuid.UUID) -> GroupDotfilesResult:
        """
        Get dotfiles for a group.

        Returns:
            GroupDotfilesResult containing dotfiles list and leftover space

        Raises:
            ProjectNotFound: If group is not found
        """
        async with self._db.begin_readonly_session() as session:
            conn = await session.connection()
            dotfiles, leftover_space = await query_group_dotfiles(conn, group_id)  # type: ignore[arg-type]
            if dotfiles is None:
                raise ProjectNotFound()
            return GroupDotfilesResult(dotfiles=dotfiles, leftover_space=leftover_space)

    async def update_dotfiles(self, group_id: uuid.UUID, dotfiles_packed: bytes) -> None:
        """Update dotfiles for a group."""
        async with self._db.begin_session() as session:
            query = (
                sa.update(GroupRow).values(dotfiles=dotfiles_packed).where(GroupRow.id == group_id)
            )
            await session.execute(query)

    async def check_user_in_group(self, user_id: uuid.UUID, group_id: uuid.UUID) -> bool:
        """Check if a user is a member of the group."""
        async with self._db.begin_readonly_session() as session:
            query = (
                sa.select(AssocGroupUserRow.group_id)
                .where(AssocGroupUserRow.user_id == user_id)
                .where(AssocGroupUserRow.group_id == group_id)
            )
            result = await session.scalar(query)
            return result is not None
