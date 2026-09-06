"""Operation scopes for endpoints."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.manager.errors.resource import ProjectNotFound
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.endpoint.row import EndpointRow
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.scopes import ExistenceCheck, OperationScope


@dataclass(frozen=True)
class ProjectDeploymentOperationScope(OperationScope):
    """Required scope for searching endpoints within a project.

    Used for project-scoped deployment search (project admin).
    """

    project_id: UUID

    @override
    def to_condition(self) -> QueryCondition:
        project_id = self.project_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EndpointRow.project == project_id

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
