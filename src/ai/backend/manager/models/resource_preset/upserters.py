from __future__ import annotations

from collections.abc import Collection, Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.data.entity.resource_preset import ResourcePresetID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.data.resource_preset.types import ResourcePresetData
from ai.backend.manager.models.resource_group.row import ResourceGroupRow
from ai.backend.manager.models.resource_preset.row import ResourcePresetRow
from ai.backend.manager.models.resource_preset.searchable_fields import (
    ResourcePresetSearchableFields,
)
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.upserter import EntityUpserter

__all__ = ("ResourcePresetUpserter",)


@dataclass
class ResourcePresetUpserter(EntityUpserter[ResourcePresetRow, ResourcePresetData]):
    """Write a resource preset under its stated id. Conflict key: id.
    Created in `global` and its resource group, or `public` while bound to none, as
    :class:`ResourcePresetCreator` is; an overwrite leaves the binding as it is."""

    id: ResourcePresetID
    name: str
    resource_slots: ResourceSlot
    shared_memory: int | None
    resource_group_id: ResourceGroupID | None

    @override
    def entity_id(self, row: ResourcePresetRow) -> ResourcePresetID:
        return ResourcePresetID(row.id)

    @override
    def created_in(self, row: ResourcePresetRow) -> Collection[EntityIdentifier]:
        beside = (
            global_entity_id(GlobalEntityName.PUBLIC)
            if self.resource_group_id is None
            else self.resource_group_id
        )
        return (global_entity_id(GlobalEntityName.GLOBAL), beside)

    @override
    def row_class(self) -> type[ResourcePresetRow]:
        return ResourcePresetRow

    @override
    def index_elements(self) -> list[str]:
        return ["id"]

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_insert_values(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "scaling_group_name": self._resource_group_name(),
            **self.build_update_values(),
        }

    @override
    def build_update_values(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "resource_slots": self.resource_slots,
            "shared_memory": self.shared_memory,
        }

    def _resource_group_name(self) -> sa.ScalarSelect[str] | None:
        if self.resource_group_id is None:
            return None
        return (
            sa.select(ResourceGroupRow.name)
            .where(ResourceGroupRow.id == self.resource_group_id)
            .scalar_subquery()
        )

    @override
    def to_data(self, row: ResourcePresetRow) -> ResourcePresetData:
        return ResourcePresetSearchableFields.own.to_data(row)
