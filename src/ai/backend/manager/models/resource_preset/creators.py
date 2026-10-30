from __future__ import annotations

from collections.abc import Collection, Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.data.entity.resource_preset import ResourcePresetID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.exception import ResourcePresetConflict
from ai.backend.common.types import BinarySize, ResourceSlot
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.data.resource_preset.types import ResourcePresetData
from ai.backend.manager.errors.repository import UniqueConstraintViolationError
from ai.backend.manager.models.resource_preset.row import ResourcePresetRow
from ai.backend.manager.models.resource_preset.searchable_fields import (
    ResourcePresetSearchableFields,
)
from ai.backend.manager.models.specs.creator import EntityCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck


@dataclass
class ResourcePresetCreator(EntityCreator[ResourcePresetRow, ResourcePresetData]):
    """Creator for one resource preset.

    Every preset belongs to `global` and to one scope beside it, decided by the resource
    group it is bound to: `public` while it is bound to none, that resource group once it
    is. The caller resolves the group's id, as the row records only its name.
    """

    name: str
    resource_slots: ResourceSlot
    shared_memory: str | None
    resource_group_name: str | None
    resource_group_id: ResourceGroupID | None = None

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
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return (
            IntegrityErrorCheck(
                violation_type=UniqueConstraintViolationError,
                error=ResourcePresetConflict(
                    f"Duplicate resource preset name (name:{self.name}, "
                    f"scaling_group:{self.resource_group_name})"
                ),
            ),
        )

    @override
    def build_row(self) -> ResourcePresetRow:
        return ResourcePresetRow(
            name=self.name,
            resource_slots=self.resource_slots,
            shared_memory=(
                int(BinarySize.from_str(self.shared_memory)) if self.shared_memory else None
            ),
            scaling_group_name=self.resource_group_name,
        )

    @override
    def to_data(self, row: ResourcePresetRow) -> ResourcePresetData:
        return ResourcePresetSearchableFields.own.to_data(row)
