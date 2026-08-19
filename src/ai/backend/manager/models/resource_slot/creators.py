from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.types import SlotTypes
from ai.backend.manager.data.resource_slot.types import ResourceSlotTypeData
from ai.backend.manager.errors.repository import UniqueConstraintViolationError
from ai.backend.manager.errors.resource_slot import ResourceSlotTypeAlreadyExists
from ai.backend.manager.models.resource_slot.row import ResourceSlotTypeRow
from ai.backend.manager.models.resource_slot.types import NumberFormat
from ai.backend.manager.models.specs.creator import GlobalEntityCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck


@dataclass
class ResourceSlotTypeCreator(GlobalEntityCreator[ResourceSlotTypeRow, ResourceSlotTypeData]):
    """Creator for a resource slot type — a global catalog row.

    Registering a name that already exists fails rather than overwriting: the
    catalog row is the FK target of five tables, so replacing one silently would
    reinterpret every quota already expressed in that slot.
    """

    slot_name: str
    slot_type: SlotTypes
    required: bool
    enabled: bool
    display_name: str
    description: str
    display_unit: str
    display_icon: str
    number_format: NumberFormat
    rank: int

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return (
            IntegrityErrorCheck(
                violation_type=UniqueConstraintViolationError,
                error=ResourceSlotTypeAlreadyExists(
                    f"Resource slot type '{self.slot_name}' already exists."
                ),
            ),
        )

    @override
    def build_row(self) -> ResourceSlotTypeRow:
        return ResourceSlotTypeRow(
            slot_name=self.slot_name,
            slot_type=self.slot_type.value,
            required=self.required,
            enabled=self.enabled,
            display_name=self.display_name,
            description=self.description,
            display_unit=self.display_unit,
            display_icon=self.display_icon,
            number_format=self.number_format,
            rank=self.rank,
        )

    @override
    def to_data(self, row: ResourceSlotTypeRow) -> ResourceSlotTypeData:
        return row.to_data()
