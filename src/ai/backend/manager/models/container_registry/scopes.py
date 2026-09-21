"""Operation scopes for container registries."""

from __future__ import annotations

from abc import ABC
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.errors.resource import ProjectNotFound
from ai.backend.manager.models.association_container_registries_groups.row import (
    AssociationContainerRegistriesGroupsRow,
)
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.container_registry.row import ContainerRegistryRow
from ai.backend.manager.models.project import ProjectRow
from ai.backend.manager.models.scopes import ExistenceCheck, ScopeTarget

__all__ = (
    "ContainerRegistryTarget",
    "ProjectContainerRegistryTarget",
    "PublicContainerRegistryTarget",
)


class ContainerRegistryTarget(ScopeTarget, ABC):
    """One side a container registry is reachable from."""


@dataclass(frozen=True)
class ProjectContainerRegistryTarget(ContainerRegistryTarget):
    """The container registries one project is linked to."""

    project_id: ProjectID

    @override
    def scope_id(self) -> EntityIdentifier:
        return self.project_id

    @override
    def to_condition(self) -> QueryCondition:
        project_id = self.project_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ContainerRegistryRow.id.in_(
                sa.select(AssociationContainerRegistriesGroupsRow.registry_id).where(
                    AssociationContainerRegistriesGroupsRow.group_id == project_id
                )
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
class PublicContainerRegistryTarget(ContainerRegistryTarget):
    """The container registries registered in public.

    `is_global` is the column that records the registration; unset is not registered.
    """

    @override
    def scope_id(self) -> EntityIdentifier:
        return global_entity_id(GlobalEntityName.PUBLIC)

    @override
    def to_condition(self) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ContainerRegistryRow.is_global.is_(True)

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return []
