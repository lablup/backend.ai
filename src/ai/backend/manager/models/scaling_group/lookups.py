"""Lookup specs for the scaling groups table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_group import ResourceGroupName
from ai.backend.manager.data.scaling_group.types import ScalingGroupData
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.scaling_group.row import ScalingGroupRow
from ai.backend.manager.models.specs.lookup import DataLookup


@dataclass
class ResourceGroupNameLookup(DataLookup[ScalingGroupRow, ScalingGroupData]):
    """Reads the resource group a name refers to."""

    name: ResourceGroupName

    @override
    def row_class(self) -> type[ScalingGroupRow]:
        return ScalingGroupRow

    @override
    def conditions(self) -> Sequence[QueryCondition]:
        return [lambda: ScalingGroupRow.name == self.name]

    @override
    def to_data(self, row: ScalingGroupRow) -> ScalingGroupData:
        return row.to_dataclass()
