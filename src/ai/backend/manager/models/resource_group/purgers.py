"""Purge specs for the scaling_groups table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.data.resource_group.types import ResourceGroupData
from ai.backend.manager.models.resource_group.row import ResourceGroupRow
from ai.backend.manager.models.specs.purger import EntityPurger
from ai.backend.manager.models.specs.types import ConflictCheck


@dataclass
class ResourceGroupPurger(EntityPurger[ResourceGroupRow, ResourceGroupData]):
    """Removes a resource group along with the scope it was."""

    resource_group_id: ResourceGroupID

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.resource_group_id

    @override
    def row_class(self) -> type[ResourceGroupRow]:
        return ResourceGroupRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return ResourceGroupRow.id

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: ResourceGroupRow) -> ResourceGroupData:
        return row.to_dataclass()
