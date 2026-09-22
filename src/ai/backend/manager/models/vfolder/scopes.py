"""Operation scopes for vfolders."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DomainEntityType, DomainID
from ai.backend.common.data.entity.project import ProjectEntityType, ProjectID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.entity.vfolder import VFolderEntityType
from ai.backend.manager.errors.resource import DomainNotFound, ProjectNotFound
from ai.backend.manager.errors.user import UserNotFound
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.project import ProjectRow
from ai.backend.manager.models.scopes import ExistenceCheck, ScopeTarget
from ai.backend.manager.models.user.queries import user_scope_reaches
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.models.virtual_entity.queries import scope_membership_exists

__all__ = (
    "DomainVFolderTarget",
    "ProjectVFolderTarget",
    "UserVFolderTarget",
)


@dataclass(frozen=True)
class DomainVFolderTarget(ScopeTarget):
    """The vfolders of one domain."""

    domain_id: DomainID

    @override
    def scope_id(self) -> EntityIdentifier:
        return self.domain_id

    @override
    def to_condition(self) -> QueryCondition:
        domain_id = self.domain_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return scope_membership_exists(
                DomainEntityType(), domain_id, VFolderEntityType(), VFolderRow.id
            )

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return [
            ExistenceCheck(
                column=DomainRow.id,
                value=self.domain_id,
                error=DomainNotFound(str(self.domain_id)),
            ),
        ]


@dataclass(frozen=True)
class ProjectVFolderTarget(ScopeTarget):
    """Required scope for searching vfolders within a project.

    Used for project-scoped vfolder search (project admin).
    """

    project_id: UUID
    """Required. The project (group) to search within."""

    @override
    def scope_id(self) -> EntityIdentifier:
        return ProjectID(self.project_id)

    @override
    def to_condition(self) -> QueryCondition:
        """Convert scope to a query condition for VFolderRow."""
        project_id = self.project_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return scope_membership_exists(
                ProjectEntityType(), project_id, VFolderEntityType(), VFolderRow.id
            )

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[UUID]]:
        """Return existence checks for scope validation."""
        return [
            ExistenceCheck(
                column=ProjectRow.id,
                value=self.project_id,
                error=ProjectNotFound(str(self.project_id)),
            ),
        ]


@dataclass(frozen=True)
class UserVFolderTarget(ScopeTarget):
    """Required scope for searching vfolders owned by a specific user.

    Used for my_vfolders query (current authenticated user).
    """

    user_id: UserID
    """Required. The user whose vfolders to search."""

    @override
    def scope_id(self) -> EntityIdentifier:
        return self.user_id

    @override
    def to_condition(self) -> QueryCondition:
        """The vfolders the user reaches: their personal project holds it, the user
        holds it directly, or one of the legacy columns still says so.

        A personal folder belongs to the user's personal project rather than to the
        user (BEP-1077), so that project is the scope this asks about.
        """
        user_id = self.user_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return user_scope_reaches(user_id, VFolderEntityType(), VFolderRow.id)

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[UUID]]:
        """Return existence checks for scope validation."""
        return [
            ExistenceCheck(
                column=UserRow.uuid,
                value=self.user_id,
                error=UserNotFound(f"User {self.user_id} not found"),
            ),
        ]
