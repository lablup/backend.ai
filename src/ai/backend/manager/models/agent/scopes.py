"""Operation scopes for agents.

An agent is created in its resource group, and the domains, projects and users linked
to that resource group read it through the relation the link records.
"""

from __future__ import annotations

from abc import ABC
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.agent import AgentEntityType
from ai.backend.common.data.entity.domain import DomainEntityType, DomainID
from ai.backend.common.data.entity.project import ProjectEntityType, ProjectID
from ai.backend.common.data.entity.resource_group import (
    ResourceGroupEntityType,
    ResourceGroupID,
)
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.errors.resource import (
    DomainNotFound,
    ProjectNotFound,
    ResourceGroupNotFound,
)
from ai.backend.manager.errors.user import UserNotFound
from ai.backend.manager.models.agent.row import AgentRow
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.resource_group.row import ResourceGroupRow
from ai.backend.manager.models.scopes import ExistenceCheck, ScopeTarget
from ai.backend.manager.models.user.queries import user_scope_reaches
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.models.virtual_entity.queries import scope_membership_exists

__all__ = (
    "AgentTarget",
    "DomainAgentTarget",
    "ProjectAgentTarget",
    "ResourceGroupAgentTarget",
    "UserAgentTarget",
)


class AgentTarget(ScopeTarget, ABC):
    """One side an agent is reachable from."""


@dataclass(frozen=True)
class ResourceGroupAgentTarget(AgentTarget):
    """The agents of one resource group."""

    resource_group_id: ResourceGroupID

    @override
    def scope_id(self) -> EntityIdentifier:
        return self.resource_group_id

    @override
    def to_condition(self) -> QueryCondition:
        resource_group_id = self.resource_group_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return scope_membership_exists(
                ResourceGroupEntityType(), resource_group_id, AgentEntityType(), AgentRow.uuid
            )

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return [
            ExistenceCheck(
                column=ResourceGroupRow.id,
                value=self.resource_group_id,
                error=ResourceGroupNotFound(str(self.resource_group_id)),
            ),
        ]


@dataclass(frozen=True)
class DomainAgentTarget(AgentTarget):
    """The agents a domain reaches through the resource groups linked to it."""

    domain_id: DomainID

    @override
    def scope_id(self) -> EntityIdentifier:
        return self.domain_id

    @override
    def to_condition(self) -> QueryCondition:
        domain_id = self.domain_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return scope_membership_exists(
                DomainEntityType(), domain_id, AgentEntityType(), AgentRow.uuid
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
class ProjectAgentTarget(AgentTarget):
    """The agents a project reaches through the resource groups linked to it."""

    project_id: ProjectID

    @override
    def scope_id(self) -> EntityIdentifier:
        return self.project_id

    @override
    def to_condition(self) -> QueryCondition:
        project_id = self.project_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return scope_membership_exists(
                ProjectEntityType(), project_id, AgentEntityType(), AgentRow.uuid
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
class UserAgentTarget(AgentTarget):
    """The agents a user reaches through the resource groups their keypairs may use."""

    user_id: UserID

    @override
    def scope_id(self) -> EntityIdentifier:
        return self.user_id

    @override
    def to_condition(self) -> QueryCondition:
        user_id = self.user_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return user_scope_reaches(user_id, AgentEntityType(), AgentRow.uuid)

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
