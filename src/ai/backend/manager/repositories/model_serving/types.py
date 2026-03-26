from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID

import sqlalchemy as sa

from ai.backend.manager.errors.resource import ProjectNotFound
from ai.backend.manager.models.endpoint.row import EndpointRow
from ai.backend.manager.models.group.row import GroupRow
from ai.backend.manager.repositories.base.types import ExistenceCheck, QueryCondition, SearchScope

__all__ = ("ProjectEndpointSearchScope",)


@dataclass(frozen=True)
class ProjectEndpointSearchScope(SearchScope):
    """Required scope for searching endpoints within a project.

    Used for project-scoped model serving search (project admin).
    """

    project_id: UUID

    def to_condition(self) -> QueryCondition:
        project_id = self.project_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EndpointRow.project == project_id

        return inner

    @property
    def existence_checks(self) -> Sequence[ExistenceCheck[UUID]]:
        return [
            ExistenceCheck(
                column=GroupRow.id,
                value=self.project_id,
                error=ProjectNotFound(str(self.project_id)),
            ),
        ]
