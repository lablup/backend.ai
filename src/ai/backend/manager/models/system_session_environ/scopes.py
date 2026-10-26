from __future__ import annotations

from abc import ABC
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DomainEntityType, DomainID
from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.project import ProjectEntityType, ProjectID
from ai.backend.common.data.entity.system_session_environ import SystemSessionEnvironEntityType
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.filter_specs import UUIDEqualMatchSpec
from ai.backend.common.data.system_session_environ.types import SystemSessionEnvironScopeType
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.errors.resource import DomainNotFound, ProjectNotFound
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.scopes import ExistenceCheck, OperationScope, ScopeTarget
from ai.backend.manager.models.system_session_environ.row import SystemSessionEnvironRow
from ai.backend.manager.models.system_session_environ.searchable_fields import (
    SystemSessionEnvironSearchableFields,
)
from ai.backend.manager.models.virtual_entity.queries import scope_membership_exists

__all__ = (
    "DomainSystemSessionEnvironTarget",
    "ProjectSystemSessionEnvironTarget",
    "PublicSystemSessionEnvironTarget",
    "SessionSystemSessionEnvironScope",
    "SystemSessionEnvironTarget",
)


class SystemSessionEnvironTarget(ScopeTarget, ABC):
    """One scope a system session environ row is reachable from."""


@dataclass(frozen=True)
class PublicSystemSessionEnvironTarget(SystemSessionEnvironTarget):
    """The rows registered in public."""

    @override
    def scope_id(self) -> EntityIdentifier:
        return global_entity_id(GlobalEntityName.PUBLIC)

    @override
    def to_condition(self) -> QueryCondition:
        return SystemSessionEnvironSearchableFields.own.scope_type.filter.equals(
            SystemSessionEnvironScopeType.PUBLIC
        )

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return ()


@dataclass(frozen=True)
class DomainSystemSessionEnvironTarget(SystemSessionEnvironTarget):
    """The rows bound to one domain itself. The graph binds a project under its domain,
    so the scope type column keeps the projects' rows out."""

    domain_id: DomainID

    @override
    def scope_id(self) -> EntityIdentifier:
        return self.domain_id

    @override
    def to_condition(self) -> QueryCondition:
        domain_id = self.domain_id
        bound_to_domain = SystemSessionEnvironSearchableFields.own.scope_type.filter.equals(
            SystemSessionEnvironScopeType.DOMAIN
        )

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.and_(
                bound_to_domain(),
                scope_membership_exists(
                    DomainEntityType(),
                    domain_id,
                    SystemSessionEnvironEntityType(),
                    SystemSessionEnvironRow.id,
                ),
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
class ProjectSystemSessionEnvironTarget(SystemSessionEnvironTarget):
    """The rows of one project."""

    project_id: ProjectID

    @override
    def scope_id(self) -> EntityIdentifier:
        return self.project_id

    @override
    def to_condition(self) -> QueryCondition:
        project_id = self.project_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return scope_membership_exists(
                ProjectEntityType(),
                project_id,
                SystemSessionEnvironEntityType(),
                SystemSessionEnvironRow.id,
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
class SessionSystemSessionEnvironScope(OperationScope):
    """The rows one session receives: ``public``, its domain's and its project's.

    Not a :class:`ScopeTarget`: the launcher reads these rows with no caller to authorize.
    """

    domain_id: DomainID
    project_id: ProjectID

    @override
    def to_condition(self) -> QueryCondition:
        fields = SystemSessionEnvironSearchableFields.own

        def bound_to_scope(
            scope_type: SystemSessionEnvironScopeType, scope_id: UUID
        ) -> sa.sql.expression.ColumnElement[bool]:
            return sa.and_(
                fields.scope_type.filter.equals(scope_type)(),
                fields.scope_id.filter.equals(UUIDEqualMatchSpec(value=scope_id, negated=False))(),
            )

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.or_(
                bound_to_scope(
                    SystemSessionEnvironScopeType.PUBLIC, global_entity_id(GlobalEntityName.PUBLIC)
                ),
                bound_to_scope(SystemSessionEnvironScopeType.DOMAIN, self.domain_id),
                bound_to_scope(SystemSessionEnvironScopeType.PROJECT, self.project_id),
            )

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return ()
