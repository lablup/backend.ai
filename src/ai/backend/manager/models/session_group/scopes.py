"""Operation scopes for session groups."""

from __future__ import annotations

from abc import ABC
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DomainEntityType, DomainID
from ai.backend.common.data.entity.project import ProjectEntityType, ProjectID
from ai.backend.common.data.entity.session_group import SessionGroupEntityType
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.errors.resource import DomainNotFound, ProjectNotFound
from ai.backend.manager.errors.user import UserNotFound
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.scopes import ExistenceCheck, ScopeTarget
from ai.backend.manager.models.session_group.row import SessionGroupRow
from ai.backend.manager.models.session_group.searchable_fields import SessionGroupSearchableFields
from ai.backend.manager.models.user.queries import user_scope_reaches
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.models.virtual_entity.queries import scope_membership_exists

__all__ = (
    "DomainSessionGroupTarget",
    "ProjectSessionGroupTarget",
    "SessionGroupTarget",
    "UserSessionGroupTarget",
)


class SessionGroupTarget(ScopeTarget, ABC):
    """One side a session group is reachable from.

    A scope reaches the groups users made, not the ones a replica group holds.
    """


@dataclass(frozen=True)
class DomainSessionGroupTarget(SessionGroupTarget):
    """The user session groups of one domain."""

    domain_id: DomainID

    @override
    def scope_id(self) -> EntityIdentifier:
        return self.domain_id

    @override
    def to_condition(self) -> QueryCondition:
        domain_id = self.domain_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.and_(
                scope_membership_exists(
                    DomainEntityType(), domain_id, SessionGroupEntityType(), SessionGroupRow.id
                ),
                SessionGroupSearchableFields.linked.replica_groups.not_exists()(),
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
class ProjectSessionGroupTarget(SessionGroupTarget):
    """The user session groups of one project."""

    project_id: ProjectID

    @override
    def scope_id(self) -> EntityIdentifier:
        return self.project_id

    @override
    def to_condition(self) -> QueryCondition:
        project_id = self.project_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.and_(
                scope_membership_exists(
                    ProjectEntityType(), project_id, SessionGroupEntityType(), SessionGroupRow.id
                ),
                SessionGroupSearchableFields.linked.replica_groups.not_exists()(),
            )

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return [
            ExistenceCheck(
                column=ProjectRow.id,
                value=self.project_id,
                error=ProjectNotFound(str(self.project_id)),
            ),
        ]


@dataclass(frozen=True)
class UserSessionGroupTarget(SessionGroupTarget):
    """The user session groups one user owns."""

    user_id: UserID

    @override
    def scope_id(self) -> EntityIdentifier:
        return self.user_id

    @override
    def to_condition(self) -> QueryCondition:
        user_id = self.user_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.and_(
                user_scope_reaches(user_id, SessionGroupEntityType(), SessionGroupRow.id),
                SessionGroupSearchableFields.linked.replica_groups.not_exists()(),
            )

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return [
            ExistenceCheck(
                column=UserRow.uuid,
                value=self.user_id,
                error=UserNotFound(f"User {self.user_id} not found"),
            ),
        ]
