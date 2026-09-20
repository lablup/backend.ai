"""Operation scopes for images."""

from __future__ import annotations

from abc import ABC
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.container_registry import (
    ContainerRegistryEntityType,
    ContainerRegistryID,
)
from ai.backend.common.data.entity.domain import DomainEntityType, DomainID
from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.image import ImageEntityType
from ai.backend.common.data.entity.project import ProjectEntityType, ProjectID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.errors.image import ContainerRegistryNotFound
from ai.backend.manager.errors.resource import DomainNotFound, ProjectNotFound
from ai.backend.manager.errors.user import UserNotFound
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.container_registry.row import ContainerRegistryRow
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.image.row import ImageRow
from ai.backend.manager.models.project import ProjectRow
from ai.backend.manager.models.scopes import ExistenceCheck, ScopeTarget
from ai.backend.manager.models.user.queries import user_scope_reaches
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.models.virtual_entity.queries import scope_membership_exists

__all__ = (
    "ContainerRegistryImageTarget",
    "DomainImageTarget",
    "ImageTarget",
    "ProjectImageTarget",
    "PublicImageTarget",
    "UserImageTarget",
)


class ImageTarget(ScopeTarget, ABC):
    """One side an image is reachable from."""


@dataclass(frozen=True)
class DomainImageTarget(ImageTarget):
    """The images of one domain."""

    domain_id: DomainID

    @override
    def scope_id(self) -> EntityIdentifier:
        return self.domain_id

    @override
    def to_condition(self) -> QueryCondition:
        domain_id = self.domain_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return scope_membership_exists(
                DomainEntityType(), domain_id, ImageEntityType(), ImageRow.id
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
class ProjectImageTarget(ImageTarget):
    """The images of one project."""

    project_id: ProjectID

    @override
    def scope_id(self) -> EntityIdentifier:
        return self.project_id

    @override
    def to_condition(self) -> QueryCondition:
        project_id = self.project_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return scope_membership_exists(
                ProjectEntityType(), project_id, ImageEntityType(), ImageRow.id
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
class UserImageTarget(ImageTarget):
    """The images one user reaches."""

    user_id: UserID

    @override
    def scope_id(self) -> EntityIdentifier:
        return self.user_id

    @override
    def to_condition(self) -> QueryCondition:
        user_id = self.user_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return user_scope_reaches(user_id, ImageEntityType(), ImageRow.id)

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
class ContainerRegistryImageTarget(ImageTarget):
    """The images of one container registry."""

    registry_id: ContainerRegistryID

    @override
    def scope_id(self) -> EntityIdentifier:
        return self.registry_id

    @override
    def to_condition(self) -> QueryCondition:
        registry_id = self.registry_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return scope_membership_exists(
                ContainerRegistryEntityType(), registry_id, ImageEntityType(), ImageRow.id
            )

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return [
            ExistenceCheck(
                column=ContainerRegistryRow.id,
                value=self.registry_id,
                error=ContainerRegistryNotFound(str(self.registry_id)),
            ),
        ]


@dataclass(frozen=True)
class PublicImageTarget(ImageTarget):
    """The images of the registries registered in public.

    `is_global` is the column that records the registration; unset is not registered.
    """

    @override
    def scope_id(self) -> EntityIdentifier:
        return global_entity_id(GlobalEntityName.PUBLIC)

    @override
    def to_condition(self) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.exists(
                sa.select(sa.literal(1))
                .select_from(ContainerRegistryRow)
                .where(
                    ContainerRegistryRow.id == ImageRow.registry_id,
                    ContainerRegistryRow.is_global.is_(True),
                )
            )

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return []
