"""Database source for project configuration operations."""

from __future__ import annotations

import uuid
from typing import Optional

import sqlalchemy as sa

from ai.backend.common import msgpack
from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.manager.errors.resource import ProjectNotFound
from ai.backend.manager.errors.storage import (
    DotfileAlreadyExists,
    DotfileCreationFailed,
    DotfileNotFound,
)
from ai.backend.manager.models.domain import MAXIMUM_DOTFILE_SIZE

# NOTE: GroupRow, AssocGroupUserRow, query_group_dotfiles are DB model names
# that intentionally retain the "group" naming from the database schema.
from ai.backend.manager.models.group import (
    AssocGroupUserRow,
    GroupRow,
    query_group_dotfiles,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.project_config.types import (
    DotfileInput,
    ProjectDotfilesResult,
    ResolvedProject,
)


class ProjectConfigDBSource:
    """Database source for project configuration operations."""

    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def resolve_group(
        self, domain_name: Optional[str], group_id_or_name: uuid.UUID | str
    ) -> ResolvedProject:
        """
        Resolve project identity (id + domain_name) in a single query.

        Uses GroupRow from the DB schema to look up project by UUID or name.

        Args:
            domain_name: Domain name (required if group_id_or_name is a string name)
            group_id_or_name: UUID or string name of the project

        Returns:
            ResolvedProject containing id and domain_name

        Raises:
            InvalidAPIParameters: If domain_name is missing when project name is provided
            ProjectNotFound: If project is not found
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
            return ResolvedProject(id=row.id, domain_name=row.domain_name)

    async def get_dotfiles(self, group_id: uuid.UUID) -> ProjectDotfilesResult:
        """
        Get dotfiles for a project.

        Returns:
            ProjectDotfilesResult containing dotfiles list and leftover space

        Raises:
            ProjectNotFound: If project is not found
        """
        async with self._db.begin_readonly_session() as session:
            conn = await session.connection()
            dotfiles, leftover_space = await query_group_dotfiles(conn, group_id)  # type: ignore[arg-type]
            if dotfiles is None:
                raise ProjectNotFound()
            return ProjectDotfilesResult(dotfiles=dotfiles, leftover_space=leftover_space)

    async def update_dotfiles(self, group_id: uuid.UUID, dotfiles_packed: bytes) -> None:
        """Update dotfiles for a project."""
        async with self._db.begin_session() as session:
            query = (
                sa.update(GroupRow).values(dotfiles=dotfiles_packed).where(GroupRow.id == group_id)
            )
            await session.execute(query)

    async def add_dotfile(self, group_id: uuid.UUID, dotfile: DotfileInput) -> None:
        """Add a new dotfile to the project in a single session."""
        async with self._db.begin_session() as session:
            conn = await session.connection()
            dotfiles, leftover_space = await query_group_dotfiles(conn, group_id)  # type: ignore[arg-type]
            if dotfiles is None:
                raise ProjectNotFound()

            if leftover_space == 0:
                raise DotfileCreationFailed("No leftover space for dotfile storage")
            if len(dotfiles) >= 100:
                raise DotfileCreationFailed("Dotfile creation limit reached")

            duplicate = [x for x in dotfiles if x["path"] == dotfile.path]
            if len(duplicate) > 0:
                raise DotfileAlreadyExists

            new_dotfiles = list(dotfiles)
            new_dotfiles.append({
                "path": dotfile.path,
                "perm": dotfile.permission,
                "data": dotfile.data,
            })
            dotfile_packed = msgpack.packb(new_dotfiles)
            if len(dotfile_packed) > MAXIMUM_DOTFILE_SIZE:
                raise DotfileCreationFailed("No leftover space for dotfile storage")

            update_query = (
                sa.update(GroupRow).values(dotfiles=dotfile_packed).where(GroupRow.id == group_id)
            )
            await session.execute(update_query)

    async def modify_dotfile(self, group_id: uuid.UUID, dotfile: DotfileInput) -> None:
        """Update an existing dotfile in the project in a single session."""
        async with self._db.begin_session() as session:
            conn = await session.connection()
            dotfiles, _ = await query_group_dotfiles(conn, group_id)  # type: ignore[arg-type]
            if dotfiles is None:
                raise ProjectNotFound()

            new_dotfiles = [x for x in dotfiles if x["path"] != dotfile.path]
            if len(new_dotfiles) == len(dotfiles):
                raise DotfileNotFound

            new_dotfiles.append({
                "path": dotfile.path,
                "perm": dotfile.permission,
                "data": dotfile.data,
            })
            dotfile_packed = msgpack.packb(new_dotfiles)
            if len(dotfile_packed) > MAXIMUM_DOTFILE_SIZE:
                raise DotfileCreationFailed("No leftover space for dotfile storage")

            update_query = (
                sa.update(GroupRow).values(dotfiles=dotfile_packed).where(GroupRow.id == group_id)
            )
            await session.execute(update_query)

    async def remove_dotfile(self, group_id: uuid.UUID, path: str) -> None:
        """Remove a dotfile from the project in a single session."""
        async with self._db.begin_session() as session:
            conn = await session.connection()
            dotfiles, _ = await query_group_dotfiles(conn, group_id)  # type: ignore[arg-type]
            if dotfiles is None:
                raise ProjectNotFound()

            new_dotfiles = [x for x in dotfiles if x["path"] != path]
            if len(new_dotfiles) == len(dotfiles):
                raise DotfileNotFound

            dotfile_packed = msgpack.packb(new_dotfiles)
            update_query = (
                sa.update(GroupRow).values(dotfiles=dotfile_packed).where(GroupRow.id == group_id)
            )
            await session.execute(update_query)

    async def check_user_in_group(self, user_id: uuid.UUID, group_id: uuid.UUID) -> bool:
        """Check if a user is a member of the project."""
        async with self._db.begin_readonly_session() as session:
            query = (
                sa.select(AssocGroupUserRow.group_id)
                .where(AssocGroupUserRow.user_id == user_id)
                .where(AssocGroupUserRow.group_id == group_id)
            )
            result = await session.scalar(query)
            return result is not None
