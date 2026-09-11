"""Write specs for a resource slot type."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from bai_scenario.seeds.seeder import Naming, SeedRow

from ai.backend.common.types import SlotTypes
from ai.backend.manager.data.resource_slot.types import ResourceSlotTypeData
from ai.backend.manager.models.resource_slot.creators import ResourceSlotTypeCreator
from ai.backend.manager.models.resource_slot.types import NumberFormat


@dataclass(frozen=True)
class SeedResourceSlotType(SeedRow[ResourceSlotTypeData]):
    """A slot type in the global catalog. Its name is what every call addresses it by."""

    name_hint: str = "slot"
    slot_type: SlotTypes = SlotTypes.COUNT
    required: bool = False
    enabled: bool = True
    display_name: str = "미리 만들어 둔 슬롯"
    description: str = "미리 만들어 둔 슬롯 종류"
    display_unit: str = ""
    display_icon: str = ""
    number_format: NumberFormat = NumberFormat()
    rank: int = 0

    @override
    def kind(self) -> str:
        return "자원 슬롯 종류"

    @override
    def detail(self) -> str:
        parts = [f"{self.slot_type.value} 종류"]
        if not self.enabled:
            parts.append("사용하지 않음")
        return ", ".join(parts)

    @override
    def name(self, naming: Naming) -> str:
        return naming(self.name_hint)

    @override
    def seed(self, name: str) -> ResourceSlotTypeCreator:
        return ResourceSlotTypeCreator(
            slot_name=name,
            slot_type=self.slot_type,
            required=self.required,
            enabled=self.enabled,
            display_name=self.display_name,
            description=self.description,
            display_unit=self.display_unit,
            display_icon=self.display_icon,
            number_format=self.number_format,
            rank=self.rank,
        )
