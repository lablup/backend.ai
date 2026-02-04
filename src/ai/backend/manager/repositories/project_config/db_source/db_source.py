"""Database source for project configuration operations.

As there is an ongoing migration of renaming group to project,
there are some occurrences where "group" is being used as "project"
(e.g., GroupRow, query_group_dotfiles, AssocGroupUserRow).
It will be fixed in the future; for now understand them as the same concept.
"""

from __future__ import annotations

import uuid

import sqlalchemy as sa

from ai.backend.common import msgpack
from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.manager.errors.auth import GroupMembershipNotFoundError, InsufficientPrivilege
from ai.backend.manager.errors.resource import ProjectNotFound
from ai.backend.manager.errors.storage import (
    DotfileAlreadyExists,
    DotfileCreationFailed,
    DotfileNotFound,
)
from ai.backend.manager.models.domain import MAXIMUM_DOTFILE_SIZE
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

    async def resolve_project(
        self, domain_name: str | None, project_id_or_name: uuid.UUID | str
    ) -> ResolvedProject:
        """
        Resolve project identity (id + domain_name) in a single query.

        Uses GroupRow from the DB schema to look up project by UUID or name.

        Args:
            domain_name: Domain name (required if project_id_or_name is a string name)
            project_id_or_name: UUID or string name of the project

        Returns:
            ResolvedProject containing id and domain_name

        Raises:
            InvalidAPIParameters: If domain_name is missing when project name is provided
            ProjectNotFound: If project is not found
        """
        async with self._db.begin_read_committed() as conn:
            if isinstance(project_id_or_name, str):
                if domain_name is None:
                    raise InvalidAPIParameters("Missing parameter 'domain'")
                query = (
                    sa.select(GroupRow.id, GroupRow.domain_name)
                    .where(GroupRow.domain_name == domain_name)
                    .where(GroupRow.name == project_id_or_name)
                )
            else:
                query = sa.select(GroupRow.id, GroupRow.domain_name).where(
                    GroupRow.id == project_id_or_name
                )
            row = (await conn.execute(query)).first()
            if row is None:
                raise ProjectNotFound()
            return ResolvedProject(id=row.id, domain_name=row.domain_name)

    async def resolve_project_for_admin(
        self,
        user_domain: str,
        is_superadmin: bool,
        domain_name: str | None,
        project_id_or_name: uuid.UUID | str,
    ) -> ResolvedProject:
        """
        Resolve project for admin operations with permission check.

        Validates that admin has permission to modify the project's dotfiles.
        Superadmins can access any project, domain admins can only access
        projects within their domain.

        Args:
            user_domain: Domain name of the requesting user
            is_superadmin: Whether the user is a superadmin
            domain_name: Domain name (required if project_id_or_name is a string name)
            project_id_or_name: UUID or string name of the project

        Returns:
            ResolvedProject containing id and domain_name

        Raises:
            InvalidAPIParameters: If domain_name is missing when project name is provided
            ProjectNotFound: If project is not found
            InsufficientPrivilege: If admin lacks permission for the project
        """
        async with self._db.begin_read_committed() as conn:
            if isinstance(project_id_or_name, str):
                if domain_name is None:
                    raise InvalidAPIParameters("Missing parameter 'domain'")
                query = (
                    sa.select(GroupRow.id, GroupRow.domain_name)
                    .where(GroupRow.domain_name == domain_name)
                    .where(GroupRow.name == project_id_or_name)
                )
            else:
                query = sa.select(GroupRow.id, GroupRow.domain_name).where(
                    GroupRow.id == project_id_or_name
                )
            row = (await conn.execute(query)).first()
            if row is None:
                raise ProjectNotFound()

            if not is_superadmin and user_domain != row.domain_name:
                raise InsufficientPrivilege(
                    "Admins cannot modify project dotfiles of other domains"
                )

            return ResolvedProject(id=row.id, domain_name=row.domain_name)

    async def resolve_project_for_user(
        self,
        user_id: uuid.UUID,
        user_domain: str,
        is_admin: bool,
        is_superadmin: bool,
        domain_name: str | None,
        project_id_or_name: uuid.UUID | str,
    ) -> ResolvedProject:
        """
        Resolve project for user operations with permission check.

        Validates that user has permission to access the project's dotfiles.
        Superadmins can access any project, domain admins can access projects
        within their domain, regular users must be members of the project.

        Args:
            user_id: UUID of the requesting user
            user_domain: Domain name of the requesting user
            is_admin: Whether the user is a domain admin
            is_superadmin: Whether the user is a superadmin
            domain_name: Domain name (required if project_id_or_name is a string name)
            project_id_or_name: UUID or string name of the project

        Returns:
            ResolvedProject containing id and domain_name

        Raises:
            InvalidAPIParameters: If domain_name is missing when project name is provided
            ProjectNotFound: If project is not found
            InsufficientPrivilege: If admin lacks permission for the project
            GroupMembershipNotFoundError: If regular user is not a member of the project
        """
        async with self._db.begin_read_committed() as conn:
            if isinstance(project_id_or_name, str):
                if domain_name is None:
                    raise InvalidAPIParameters("Missing parameter 'domain'")
                query = (
                    sa.select(GroupRow.id, GroupRow.domain_name)
                    .where(GroupRow.domain_name == domain_name)
                    .where(GroupRow.name == project_id_or_name)
                )
            else:
                query = sa.select(GroupRow.id, GroupRow.domain_name).where(
                    GroupRow.id == project_id_or_name
                )
            row = (await conn.execute(query)).first()
            if row is None:
                raise ProjectNotFound()

            if is_superadmin:
                return ResolvedProject(id=row.id, domain_name=row.domain_name)

            if is_admin:
                if user_domain != row.domain_name:
                    raise InsufficientPrivilege(
                        "Domain admins cannot access project dotfiles of other domains"
                    )
                return ResolvedProject(id=row.id, domain_name=row.domain_name)

            # Regular user: check membership
            membership_query = (
                sa.select(AssocGroupUserRow.group_id)
                .where(AssocGroupUserRow.user_id == user_id)
                .where(AssocGroupUserRow.group_id == row.id)
            )
            membership_result = await conn.scalar(membership_query)
            if membership_result is None:
                raise GroupMembershipNotFoundError(
                    "User cannot access project dotfiles of non-member projects"
                )

            return ResolvedProject(id=row.id, domain_name=row.domain_name)

    async def get_dotfiles(self, project_id: uuid.UUID) -> ProjectDotfilesResult:
        """
        Get dotfiles for a project.

        Returns:
            ProjectDotfilesResult containing dotfiles list and leftover space

        Raises:
            DotfileNotFound: If project has no dotfiles configured
        """
        async with self._db.begin_read_committed() as conn:
            dotfiles, leftover_space = await query_group_dotfiles(conn, project_id)
            if dotfiles is None:
                raise DotfileNotFound
            return ProjectDotfilesResult(dotfiles=dotfiles, leftover_space=leftover_space)

    async def update_dotfiles(self, project_id: uuid.UUID, dotfiles_packed: bytes) -> None:
        """Update dotfiles for a project."""
        async with self._db.begin_session_read_committed() as session:
            query = (
                sa.update(GroupRow)
                .values(dotfiles=dotfiles_packed)
                .where(GroupRow.id == project_id)
            )
            await session.execute(query)

    async def add_dotfile(self, project_id: uuid.UUID, dotfile: DotfileInput) -> None:
        """Add a new dotfile to the project in a single session."""
        async with self._db.begin_session_read_committed() as session:
            conn = await session.connection()
            dotfiles, leftover_space = await query_group_dotfiles(conn, project_id)
            if dotfiles is None:
                raise DotfileNotFound

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
                sa.update(GroupRow).values(dotfiles=dotfile_packed).where(GroupRow.id == project_id)
            )
            await session.execute(update_query)

    async def modify_dotfile(self, project_id: uuid.UUID, dotfile: DotfileInput) -> None:
        """Update an existing dotfile in the project in a single session."""
        async with self._db.begin_session_read_committed() as session:
            conn = await session.connection()
            dotfiles, _ = await query_group_dotfiles(conn, project_id)
            if dotfiles is None:
                raise DotfileNotFound

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
                sa.update(GroupRow).values(dotfiles=dotfile_packed).where(GroupRow.id == project_id)
            )
            await session.execute(update_query)

    async def remove_dotfile(self, project_id: uuid.UUID, path: str) -> None:
        """Remove a dotfile from the project in a single session."""
        async with self._db.begin_session_read_committed() as session:
            conn = await session.connection()
            dotfiles, _ = await query_group_dotfiles(conn, project_id)
            if dotfiles is None:
                raise DotfileNotFound

            new_dotfiles = [x for x in dotfiles if x["path"] != path]
            if len(new_dotfiles) == len(dotfiles):
                raise DotfileNotFound

            dotfile_packed = msgpack.packb(new_dotfiles)
            update_query = (
                sa.update(GroupRow).values(dotfiles=dotfile_packed).where(GroupRow.id == project_id)
            )
            await session.execute(update_query)

    async def check_user_in_project(self, user_id: uuid.UUID, project_id: uuid.UUID) -> bool:
        """Check if a user is a member of the project."""
        async with self._db.begin_read_committed() as conn:
            query = (
                sa.select(AssocGroupUserRow.group_id)
                .where(AssocGroupUserRow.user_id == user_id)
                .where(AssocGroupUserRow.group_id == project_id)
            )
            result = await conn.scalar(query)
            return result is not None
