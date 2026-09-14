"""Operation scopes for model cards."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.entity.model_card import ModelCardEntityType, ModelCardID
from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.manager.errors.resource import ProjectNotFound
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.model_card.row import ModelCardRow
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.resource_slot.row import ModelCardResourceRequirementRow
from ai.backend.manager.models.scopes import ExistenceCheck, OperationScope
from ai.backend.manager.models.virtual_entity.queries import scope_membership_exists

__all__ = (
    "ModelCardResourceRequirementOperationScope",
    "ProjectModelCardOperationScope",
    "VFolderModelCardOperationScope",
)


@dataclass
class ModelCardResourceRequirementOperationScope(OperationScope):
    """The minimum quantities one card declares."""

    model_card_id: ModelCardID

    @override
    def to_condition(self) -> QueryCondition:
        model_card_id = self.model_card_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ModelCardResourceRequirementRow.model_card_id == model_card_id

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return ()


@dataclass(frozen=True)
class ProjectModelCardOperationScope(OperationScope):
    """Scope for searching model cards within a MODEL_STORE project."""

    project_id: UUID

    @override
    def to_condition(self) -> QueryCondition:
        project_id = self.project_id

        # TODO(BA-7571): drop the column term once the ownership backfill lands.
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.or_(
                ModelCardRow.project == project_id,
                scope_membership_exists(
                    ProjectEntityType(), project_id, ModelCardEntityType(), ModelCardRow.id
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
