"""Operation scopes for endpoints."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.entity.deployment import DeploymentEntityType, DeploymentID
from ai.backend.common.data.entity.project import PROJECT_SCOPE_TYPE
from ai.backend.common.data.entity.user import USER_SCOPE_TYPE
from ai.backend.manager.errors.resource import ProjectNotFound
from ai.backend.manager.errors.user import UserNotFound
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.endpoint.row import EndpointRow, EndpointTokenRow
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.scopes import ExistenceCheck, OperationScope
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.models.virtual_entity.queries import scope_membership_exists


@dataclass(frozen=True)
class ProjectDeploymentOperationScope(OperationScope):
    """Required scope for searching endpoints within a project.

    Used for project-scoped deployment search (project admin).
    """

    project_id: UUID

    @override
    def to_condition(self) -> QueryCondition:
        project_id = self.project_id

        # TODO(BA-7571): drop the column term once the ownership backfill lands.
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.or_(
                EndpointRow.project == project_id,
                scope_membership_exists(
                    PROJECT_SCOPE_TYPE, project_id, DeploymentEntityType(), EndpointRow.id
                ),
            )

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[UUID]]:
        return [
            ExistenceCheck(
                column=ProjectRow.id,
                value=self.project_id,
                error=ProjectNotFound(str(self.project_id)),
            ),
        ]


@dataclass(frozen=True)
class UserDeploymentOperationScope(OperationScope):
    """The deployments one user created."""

    user_id: UUID

    @override
    def to_condition(self) -> QueryCondition:
        user_id = self.user_id

        # TODO(BA-7571): drop the column term once the ownership backfill lands.
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.or_(
                EndpointRow.created_user == user_id,
                scope_membership_exists(
                    USER_SCOPE_TYPE, user_id, DeploymentEntityType(), EndpointRow.id
                ),
            )

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[UUID]]:
        return [
            ExistenceCheck(
                column=UserRow.uuid,
                value=self.user_id,
                error=UserNotFound(f"User {self.user_id} not found"),
            ),
        ]


@dataclass(frozen=True)
class DeploymentAccessTokenOperationScope(OperationScope):
    """The access tokens one deployment holds."""

    deployment_id: DeploymentID

    @override
    def to_condition(self) -> QueryCondition:
        deployment_id = self.deployment_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EndpointTokenRow.endpoint == deployment_id

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return ()
