"""Operation scopes for sessions."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.entity.project import PROJECT_SCOPE_TYPE
from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.manager.errors.resource import ProjectNotFound
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.scopes import ExistenceCheck, OperationScope
from ai.backend.manager.models.session.row import SessionRow
from ai.backend.manager.models.virtual_entity.queries import scope_membership_exists

__all__ = ("ProjectSessionOperationScope",)


@dataclass(frozen=True)
class ProjectSessionOperationScope(OperationScope):
    """Required scope for searching sessions within a project.

    Used for project-scoped session search (project admin).
    """

    project_id: UUID
    """Required. The project (group) to search within."""

    @override
    def to_condition(self) -> QueryCondition:
        """Convert scope to a query condition for SessionRow."""
        project_id = self.project_id

        # TODO(BA-7571): drop the column term once the ownership backfill lands.
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.or_(
                SessionRow.group_id == project_id,
                scope_membership_exists(
                    PROJECT_SCOPE_TYPE, project_id, SessionEntityType(), SessionRow.id
                ),
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
