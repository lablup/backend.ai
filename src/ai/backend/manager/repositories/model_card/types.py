"""Types for model card repository operations."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID

import sqlalchemy as sa

from ai.backend.manager.data.deployment_revision_preset.types import DeploymentRevisionPresetData
from ai.backend.manager.data.model_card.types import ModelCardData
from ai.backend.manager.errors.resource import ProjectNotFound
from ai.backend.manager.models.group.row import AssocGroupUserRow, GroupRow
from ai.backend.manager.models.model_card.row import ModelCardRow
from ai.backend.manager.repositories.base import ExistenceCheck, QueryCondition, SearchScope

__all__ = (
    "AvailablePresetsSearchResult",
    "ModelCardSearchResult",
    "ProjectModelCardSearchScope",
)


@dataclass
class AvailablePresetsSearchResult:
    """Result from searching available presets for a model card."""

    items: list[DeploymentRevisionPresetData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool


@dataclass
class ModelCardSearchResult:
    """Result from searching model cards."""

    items: list[ModelCardData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool


@dataclass(frozen=True)
class ProjectModelCardSearchScope(SearchScope):
    """Scope for searching model cards within a MODEL_STORE project.

    Includes user_id for membership validation — only project members
    can search model cards in the project.
    """

    project_id: UUID
    user_id: UUID

    def to_condition(self) -> QueryCondition:
        project_id = self.project_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ModelCardRow.project == project_id

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

    @property
    def membership_check_query(self) -> sa.Select[tuple[bool]]:
        """Query to validate user is a member of this project."""
        return sa.select(sa.literal(True)).where(
            sa.and_(
                AssocGroupUserRow.user_id == self.user_id,
                AssocGroupUserRow.group_id == self.project_id,
            )
        )
