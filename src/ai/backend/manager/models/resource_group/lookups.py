"""Lookup specs for the scaling groups table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.entity.resource_group import (
    ResourceGroupEntityType,
    ResourceGroupID,
    ResourceGroupName,
)
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.resource_group.row import ResourceGroupRow
from ai.backend.manager.models.specs.lookup import BulkDataLookup, DataLookup


@dataclass
class ResourceGroupNameLookup(DataLookup[ResourceGroupRow, ResourceGroupID]):
    """Reads the resource group a name refers to."""

    name: ResourceGroupName

    @override
    def row_class(self) -> type[ResourceGroupRow]:
        return ResourceGroupRow

    @override
    def entity_type(self) -> EntityType:
        return ResourceGroupEntityType()

    @override
    def conditions(self) -> Sequence[QueryCondition]:
        return [lambda: ResourceGroupRow.name == self.name]

    @override
    def to_entity_id(self, row: ResourceGroupRow) -> ResourceGroupID:
        return row.id


@dataclass
class ResourceGroupNamesLookup(BulkDataLookup[ResourceGroupName, ResourceGroupID]):
    """Resolves several names into the resource groups they refer to."""

    @override
    def build_query(self, keys: Sequence[ResourceGroupName]) -> sa.sql.Select[Any]:
        return sa.select(ResourceGroupRow.name, ResourceGroupRow.id).where(
            ResourceGroupRow.name.in_(keys)
        )

    @override
    def to_entity_id(self, value: UUID) -> ResourceGroupID:
        return ResourceGroupID(value)
