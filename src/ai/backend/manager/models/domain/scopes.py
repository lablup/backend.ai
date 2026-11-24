"""Operation scopes for domains."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.errors.image import ContainerRegistryNotFound
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.container_registry.row import ContainerRegistryRow
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.domain_container_registry_relation.row import (
    DomainContainerRegistryRelationRow,
)
from ai.backend.manager.models.resource_group.row import ResourceGroupForDomainRow
from ai.backend.manager.models.scopes import ExistenceCheck, ScopeTarget

__all__ = (
    "ContainerRegistryDomainTarget",
    "ResourceGroupDomainTarget",
)


@dataclass(frozen=True)
class ResourceGroupDomainTarget(ScopeTarget):
    """The domains a resource group serves."""

    resource_group_id: ResourceGroupID

    @override
    def scope_id(self) -> EntityIdentifier:
        return self.resource_group_id

    @override
    def to_condition(self) -> QueryCondition:
        resource_group_id = self.resource_group_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DomainRow.id.in_(
                sa.select(ResourceGroupForDomainRow.domain_id).where(
                    ResourceGroupForDomainRow.resource_group_id == resource_group_id
                )
            )

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return ()


@dataclass(frozen=True)
class ContainerRegistryDomainTarget(ScopeTarget):
    """The domains one container registry is related to."""

    container_registry_id: ContainerRegistryID

    @override
    def scope_id(self) -> EntityIdentifier:
        return self.container_registry_id

    @override
    def to_condition(self) -> QueryCondition:
        container_registry_id = self.container_registry_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DomainRow.id.in_(
                sa.select(DomainContainerRegistryRelationRow.domain_id).where(
                    DomainContainerRegistryRelationRow.container_registry_id
                    == container_registry_id
                )
            )

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return [
            ExistenceCheck(
                column=ContainerRegistryRow.id,
                value=self.container_registry_id,
                error=ContainerRegistryNotFound(str(self.container_registry_id)),
            ),
        ]
