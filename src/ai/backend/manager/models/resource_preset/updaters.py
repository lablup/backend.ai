from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.resource_preset import ResourcePresetID
from ai.backend.common.types import BinarySize, ResourceSlot
from ai.backend.manager.data.resource_preset.types import ResourcePresetData
from ai.backend.manager.models.resource_preset.row import ResourcePresetRow
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import DataUpdater
from ai.backend.manager.types import OptionalState, TriState


@dataclass
class ResourcePresetUpdater(DataUpdater[ResourcePresetRow, ResourcePresetData]):
    """Updater for one resource preset."""

    preset_id: ResourcePresetID
    resource_slots: OptionalState[ResourceSlot] = field(
        default_factory=OptionalState[ResourceSlot].nop
    )
    name: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    shared_memory: TriState[BinarySize] = field(default_factory=TriState[BinarySize].nop)
    resource_group_name: TriState[str] = field(default_factory=TriState[str].nop)

    @property
    @override
    def row_class(self) -> type[ResourcePresetRow]:
        return ResourcePresetRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return ResourcePresetRow.id

    @override
    def target_id_value(self) -> ResourcePresetID:
        return self.preset_id

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.resource_slots.update_dict(to_update, "resource_slots")
        self.name.update_dict(to_update, "name")
        self.shared_memory.update_dict(to_update, "shared_memory")
        self.resource_group_name.update_dict(to_update, "scaling_group_name")
        return to_update

    @override
    def to_data(self, row: ResourcePresetRow) -> ResourcePresetData:
        return row.to_dataclass()
