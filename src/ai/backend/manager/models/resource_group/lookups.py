"""Lookup specs for the scaling groups table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_group import ResourceGroupID, ResourceGroupName
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.resource_group.row import ResourceGroupRow
from ai.backend.manager.models.specs.lookup import DataLookup


@dataclass
class ResourceGroupNameLookup(DataLookup[ResourceGroupRow, ResourceGroupID]):
    """Reads the resource group a name refers to."""

    name: ResourceGroupName

    @override
    def row_class(self) -> type[ResourceGroupRow]:
        return ResourceGroupRow

    @override
    def conditions(self) -> Sequence[QueryCondition]:
        return [lambda: ResourceGroupRow.name == self.name]

    @override
    def to_entity_id(self, row: ResourceGroupRow) -> ResourceGroupID:
        return row.id
