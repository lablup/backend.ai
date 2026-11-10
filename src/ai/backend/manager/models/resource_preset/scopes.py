"""Operation scopes for resource presets."""

from __future__ import annotations

from abc import ABC
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.errors.resource import ResourceGroupNotFound
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.resource_group.row import ResourceGroupRow
from ai.backend.manager.models.resource_preset.row import ResourcePresetRow
from ai.backend.manager.models.scopes import ExistenceCheck, ScopeTarget

__all__ = (
    "PublicResourcePresetTarget",
    "ResourceGroupResourcePresetTarget",
    "ResourcePresetTarget",
)


class ResourcePresetTarget(ScopeTarget, ABC):
    """One side a resource preset is reachable from."""


@dataclass(frozen=True)
class ResourceGroupResourcePresetTarget(ResourcePresetTarget):
    """The presets bound to one resource group.

    `scaling_group_name` is the column that records the binding; the name is read off the
    resource group the id names, so the caller names the group the read is authorized
    against.
    """

    resource_group_id: ResourceGroupID

    @override
    def scope_id(self) -> EntityIdentifier:
        return self.resource_group_id

    @override
    def to_condition(self) -> QueryCondition:
        resource_group_id = self.resource_group_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ResourcePresetRow.scaling_group_name.in_(
                sa.select(ResourceGroupRow.name).where(ResourceGroupRow.id == resource_group_id)
            )

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return [
            ExistenceCheck(
                column=ResourceGroupRow.id,
                value=self.resource_group_id,
                error=ResourceGroupNotFound(str(self.resource_group_id)),
            ),
        ]


@dataclass(frozen=True)
class PublicResourcePresetTarget(ResourcePresetTarget):
    """The presets bound to no resource group, which every user is offered."""

    @override
    def scope_id(self) -> EntityIdentifier:
        return global_entity_id(GlobalEntityName.PUBLIC)

    @override
    def to_condition(self) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ResourcePresetRow.scaling_group_name.is_(None)

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return []
