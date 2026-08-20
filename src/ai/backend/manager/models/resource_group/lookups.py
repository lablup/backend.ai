"""Lookup specs for the scaling groups table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_group import ResourceGroupName
from ai.backend.manager.data.resource_group.types import ResourceGroupData
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.resource_group.row import ResourceGroupRow
from ai.backend.manager.models.specs.lookup import DataLookup


@dataclass
class ResourceGroupNameLookup(DataLookup[ResourceGroupRow, ResourceGroupData]):
    """Reads the resource group a name refers to."""

    name: ResourceGroupName

    @override
    def row_class(self) -> type[ResourceGroupRow]:
        return ResourceGroupRow

    @override
    def conditions(self) -> Sequence[QueryCondition]:
        return [lambda: ResourceGroupRow.name == self.name]

    @override
    def to_data(self, row: ResourceGroupRow) -> ResourceGroupData:
        return row.to_dataclass()
