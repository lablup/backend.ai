"""Types for vfolder repository operations."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID

import sqlalchemy as sa

from ai.backend.manager.errors.resource import ProjectNotFound
from ai.backend.manager.errors.user import UserNotFound
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.models.vfolder import VFolderPermissionRow, VFolderRow
from ai.backend.manager.repositories.base import ExistenceCheck, QueryCondition, SearchScope

__all__ = (
    "ProjectVFolderSearchScope",
    "UserVFolderSearchScope",
)


@dataclass(frozen=True)
class ProjectVFolderSearchScope(SearchScope):
    """Required scope for searching vfolders within a project.

    Used for project-scoped vfolder search (project admin).
    """

    project_id: UUID
    """Required. The project (group) to search within."""

    def to_condition(self) -> QueryCondition:
        """Convert scope to a query condition for VFolderRow."""
        project_id = self.project_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return VFolderRow.group == project_id

        return inner

    @property
    def existence_checks(self) -> Sequence[ExistenceCheck[UUID]]:
        """Return existence checks for scope validation."""
        return [
            ExistenceCheck(
                column=GroupRow.id,
                value=self.project_id,
                error=ProjectNotFound(str(self.project_id)),
            ),
        ]


@dataclass(frozen=True)
class UserVFolderSearchScope(SearchScope):
    """Required scope for searching vfolders owned by a specific user.

    Used for my_vfolders query (current authenticated user).
    """

    user_id: UUID
    """Required. The user whose vfolders to search."""

    def to_condition(self) -> QueryCondition:
        """Convert scope to a query condition for VFolderRow.

        Returns vfolders where the user is the owner (VFolderRow.user)
        OR has been granted permission (via VFolderPermissionRow).
        """
        user_id = self.user_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            permitted_vfolder_ids = sa.select(VFolderPermissionRow.vfolder).where(
                VFolderPermissionRow.user == user_id
            )
            return sa.or_(
                VFolderRow.user == user_id,
                VFolderRow.id.in_(permitted_vfolder_ids),
            )

        return inner

    @property
    def existence_checks(self) -> Sequence[ExistenceCheck[UUID]]:
        """Return existence checks for scope validation."""
        return [
            ExistenceCheck(
                column=UserRow.uuid,
                value=self.user_id,
                error=UserNotFound(f"User {self.user_id} not found"),
            ),
        ]
