"""Write specs for a resource slot type."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.types import IntrinsicSlotNames, SlotTypes
from ai.backend.manager.data.resource_slot.types import ResourceSlotTypeData
from ai.backend.manager.models.resource_slot.creators import ResourceSlotTypeCreator
from ai.backend.manager.models.resource_slot.types import NumberFormat
from bai_scenario.seeds.seeder import Naming, SeedRow


@dataclass(frozen=True)
class SeedSlotType(SeedRow[ResourceSlotTypeData]):
    """A slot type in the global catalog.

    The manager fixes the name, so the row answers with it. A slot a revision allocates
    must stand here first.
    """

    slot: IntrinsicSlotNames
    required: bool = False

    @override
    def kind(self) -> str:
        return "자원 슬롯 타입"

    @override
    def detail(self) -> str:
        if self.required:
            return "모든 리비전이 반드시 채워야 한다"
        return "리비전이 채우지 않아도 된다"

    @override
    def name(self, naming: Naming) -> str:
        return str(self.slot.value)

    @override
    def seed(self, name: str) -> ResourceSlotTypeCreator:
        return ResourceSlotTypeCreator(
            slot_name=name,
            slot_type=(SlotTypes.COUNT if self.slot == IntrinsicSlotNames.CPU else SlotTypes.BYTES),
            required=self.required,
            enabled=True,
            display_name=name,
            description="",
            display_unit="",
            display_icon="",
            number_format=NumberFormat(),
            rank=0,
        )
