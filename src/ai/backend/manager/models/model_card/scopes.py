"""Operation scopes for model cards."""

from __future__ import annotations

from abc import ABC
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DomainEntityType, DomainID
from ai.backend.common.data.entity.model_card import ModelCardEntityType, ModelCardID
from ai.backend.common.data.entity.project import ProjectEntityType, ProjectID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.errors.resource import DomainNotFound, ProjectNotFound
from ai.backend.manager.errors.user import UserNotFound
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.model_card.row import ModelCardRow
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.resource_slot.row import ModelCardResourceRequirementRow
from ai.backend.manager.models.scopes import ExistenceCheck, ScopeTarget
from ai.backend.manager.models.user.queries import user_scope_reaches
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.models.virtual_entity.queries import scope_membership_exists

__all__ = (
    "DomainModelCardTarget",
    "ModelCardResourceRequirementTarget",
    "ModelCardTarget",
    "ProjectModelCardTarget",
    "UserModelCardTarget",
)


@dataclass
class ModelCardResourceRequirementTarget(ScopeTarget):
    """The minimum quantities one card declares."""

    model_card_id: ModelCardID

    @override
    def scope_id(self) -> EntityIdentifier:
        return self.model_card_id

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


class ModelCardTarget(ScopeTarget, ABC):
    """One side a model card is reachable from."""


@dataclass(frozen=True)
class DomainModelCardTarget(ModelCardTarget):
    """The model cards of one domain."""

    domain_id: DomainID

    @override
    def scope_id(self) -> EntityIdentifier:
        return self.domain_id

    @override
    def to_condition(self) -> QueryCondition:
        domain_id = self.domain_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return scope_membership_exists(
                DomainEntityType(), domain_id, ModelCardEntityType(), ModelCardRow.id
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
class UserModelCardTarget(ModelCardTarget):
    """The model cards one user holds.

    Read from the membership edge alone: `creator` records who the card came into
    being for, which is provenance rather than ownership.
    """

    user_id: UserID

    @override
    def scope_id(self) -> EntityIdentifier:
        return self.user_id

    @override
    def to_condition(self) -> QueryCondition:
        user_id = self.user_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return user_scope_reaches(user_id, ModelCardEntityType(), ModelCardRow.id)

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


@dataclass(frozen=True)
class ProjectModelCardTarget(ModelCardTarget):
    """Scope for searching model cards within a MODEL_STORE project."""

    project_id: UUID

    @override
    def scope_id(self) -> EntityIdentifier:
        return ProjectID(self.project_id)

    @override
    def to_condition(self) -> QueryCondition:
        project_id = self.project_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return scope_membership_exists(
                ProjectEntityType(), project_id, ModelCardEntityType(), ModelCardRow.id
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
