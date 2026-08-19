"""DataUpdater implementations for the resource slot repository."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.manager.data.resource_slot.types import ResourceSlotTypeData
from ai.backend.manager.models.resource_slot.row import ResourceSlotTypeRow
from ai.backend.manager.models.resource_slot.types import NumberFormat
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import DataUpdater
from ai.backend.manager.types import OptionalState


@dataclass
class ResourceSlotTypeUpdater(DataUpdater[ResourceSlotTypeRow, ResourceSlotTypeData]):
    """Updater for a resource slot type, keyed by its ``slot_name`` primary key.

    ``slot_name`` and ``slot_type`` are absent on purpose: the name is the FK target
    of five tables, and the type decides how every quota already stored in the slot
    is read.
    """

    slot_name: str
    required: OptionalState[bool] = field(default_factory=OptionalState[bool].nop)
    enabled: OptionalState[bool] = field(default_factory=OptionalState[bool].nop)
    display_name: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    description: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    display_unit: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    display_icon: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    number_format: OptionalState[NumberFormat] = field(
        default_factory=OptionalState[NumberFormat].nop
    )
    rank: OptionalState[int] = field(default_factory=OptionalState[int].nop)

    @property
    @override
    def row_class(self) -> type[ResourceSlotTypeRow]:
        return ResourceSlotTypeRow

    @override
    def pk_value(self) -> str:
        return self.slot_name

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.required.update_dict(to_update, "required")
        self.enabled.update_dict(to_update, "enabled")
        self.display_name.update_dict(to_update, "display_name")
        self.description.update_dict(to_update, "description")
        self.display_unit.update_dict(to_update, "display_unit")
        self.display_icon.update_dict(to_update, "display_icon")
        self.number_format.update_dict(to_update, "number_format")
        self.rank.update_dict(to_update, "rank")
        return to_update

    @override
    def to_data(self, row: ResourceSlotTypeRow) -> ResourceSlotTypeData:
        return row.to_data()
