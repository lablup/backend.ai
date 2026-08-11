"""Types for model card repository operations."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.entity.project import PROJECT_SCOPE_TYPE
from ai.backend.common.identifier.vfolder import VFolderUUID
from ai.backend.manager.data.deployment_revision_preset.types import DeploymentRevisionPresetData
from ai.backend.manager.data.model_card.types import ModelCardData
from ai.backend.manager.errors.resource import ProjectNotFound
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.group.row import GroupRow
from ai.backend.manager.models.model_card.row import ModelCardRow
from ai.backend.manager.models.scopes import ExistenceCheck, OperationScope
from ai.backend.manager.models.virtual_scope.queries import user_scope_membership_exists

__all__ = (
    "AvailablePresetsSearchResult",
    "ModelCardSearchResult",
    "ProjectModelCardOperationScope",
    "VFolderModelCardOperationScope",
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
class ProjectModelCardOperationScope(OperationScope):
    """Scope for searching model cards within a MODEL_STORE project.

    Includes user_id for membership validation — only project members
    can search model cards in the project.
    """

    project_id: UUID
    user_id: UUID

    @override
    def to_condition(self) -> QueryCondition:
        project_id = self.project_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ModelCardRow.project == project_id

        return inner

    @property
    @override
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
        return sa.select(
            user_scope_membership_exists(PROJECT_SCOPE_TYPE, self.project_id, self.user_id)
        )


@dataclass(frozen=True)
class VFolderModelCardOperationScope(OperationScope):
    """Scope for searching model cards backed by a specific VFolder.

    Access is delegated to the parent VFolder resolver — if the caller
    can resolve the VFolder, they may see model cards backed by it.
    """

    vfolder_id: VFolderUUID

    @override
    def to_condition(self) -> QueryCondition:
        vfolder_id = self.vfolder_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ModelCardRow.vfolder == vfolder_id

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[UUID]]:
        return ()
