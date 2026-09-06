"""Operation scopes for resource usage history."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.errors.resource import (
    DomainNotFound,
    ProjectNotFound,
    ResourceGroupNotFound,
)
from ai.backend.manager.errors.user import UserNotFound
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.project import ProjectRow
from ai.backend.manager.models.resource_group import ResourceGroupRow
from ai.backend.manager.models.resource_usage_history import (
    DomainUsageBucketRow,
    ProjectUsageBucketRow,
    UserUsageBucketRow,
)
from ai.backend.manager.models.scopes import ExistenceCheck, OperationScope
from ai.backend.manager.models.user import UserRow


@dataclass(frozen=True)
class DomainUsageBucketOperationScope(OperationScope):
    """Scope for domain usage bucket queries."""

    resource_group: str
    domain_name: str

    @override
    def to_condition(self) -> QueryCondition:
        resource_group = self.resource_group
        domain_name = self.domain_name

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.and_(
                DomainUsageBucketRow.domain_name == domain_name,
                DomainUsageBucketRow.resource_group == resource_group,
            )

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return [
            ExistenceCheck(
                column=ResourceGroupRow.name,
                value=self.resource_group,
                error=ResourceGroupNotFound(self.resource_group),
            ),
            ExistenceCheck(
                column=DomainRow.name,
                value=self.domain_name,
                error=DomainNotFound(self.domain_name),
            ),
        ]


@dataclass(frozen=True)
class ProjectUsageBucketOperationScope(OperationScope):
    """Scope for project usage bucket queries."""

    resource_group: str
    domain_name: str
    project_id: uuid.UUID

    @override
    def to_condition(self) -> QueryCondition:
        resource_group = self.resource_group
        domain_name = self.domain_name
        project_id = self.project_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.and_(
                ProjectUsageBucketRow.domain_name == domain_name,
                ProjectUsageBucketRow.project_id == project_id,
                ProjectUsageBucketRow.resource_group == resource_group,
            )

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return [
            ExistenceCheck(
                column=ResourceGroupRow.name,
                value=self.resource_group,
                error=ResourceGroupNotFound(self.resource_group),
            ),
            ExistenceCheck(
                column=DomainRow.name,
                value=self.domain_name,
                error=DomainNotFound(self.domain_name),
            ),
            ExistenceCheck(
                column=ProjectRow.id,
                value=self.project_id,
                error=ProjectNotFound(extra_data={"project_id": str(self.project_id)}),
            ),
        ]


@dataclass(frozen=True)
class UserUsageBucketOperationScope(OperationScope):
    """Scope for user usage bucket queries."""

    resource_group: str
    domain_name: str
    project_id: uuid.UUID
    user_uuid: uuid.UUID

    @override
    def to_condition(self) -> QueryCondition:
        resource_group = self.resource_group
        domain_name = self.domain_name
        project_id = self.project_id
        user_uuid = self.user_uuid

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.and_(
                UserUsageBucketRow.domain_name == domain_name,
                UserUsageBucketRow.project_id == project_id,
                UserUsageBucketRow.user_uuid == user_uuid,
                UserUsageBucketRow.resource_group == resource_group,
            )

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return [
            ExistenceCheck(
                column=ResourceGroupRow.name,
                value=self.resource_group,
                error=ResourceGroupNotFound(self.resource_group),
            ),
            ExistenceCheck(
                column=DomainRow.name,
                value=self.domain_name,
                error=DomainNotFound(self.domain_name),
            ),
            ExistenceCheck(
                column=ProjectRow.id,
                value=self.project_id,
                error=ProjectNotFound(extra_data={"project_id": str(self.project_id)}),
            ),
            ExistenceCheck(
                column=UserRow.uuid,
                value=self.user_uuid,
                error=UserNotFound(extra_data={"user_uuid": str(self.user_uuid)}),
            ),
        ]
