"""Write specs for a resource slot type."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.types import IntrinsicSlotNames, SlotTypes
from ai.backend.manager.data.resource_slot.types import ResourceSlotTypeData
from ai.backend.manager.models.resource_slot.creators import ResourceSlotTypeCreator
from ai.backend.manager.models.resource_slot.types import NumberFormat
from ai.backend.testutils.scenario_steps import Says
from bai_scenario.seeds.seeder import Naming, TestSeedRow, joined


@dataclass(frozen=True)
class TestSeedSlotType(TestSeedRow[ResourceSlotTypeData]):
    """A slot type in the global catalog.

    The manager fixes the name, so the row answers with it. A slot a revision allocates
    must stand here first.
    """

    slot: IntrinsicSlotNames
    required: bool = False

    @override
    def kind(self) -> str:
        return Says("자원 슬롯 유형", english="Resource slot type")

    @override
    def detail(self) -> str:
        if self.required:
            return Says(
                "모든 리비전이 반드시 채워야 합니다",
                english="every revision must fill it",
            )
        return Says("리비전이 채우지 않아도 됩니다", english="a revision may leave it unfilled")

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
            sealed_launch=False,
        )


@dataclass(frozen=True)
class TestSeedResourceSlotType(TestSeedRow[ResourceSlotTypeData]):
    """A slot type in the global catalog. Its name is what every call addresses it by."""

    name_hint: str = "slot"
    slot_type: SlotTypes = SlotTypes.COUNT
    required: bool = False
    enabled: bool = True
    display_name: str = Says("미리 저장한 슬롯", english="a slot prepared in advance")
    description: str = Says("미리 저장한 슬롯 종류", english="a slot type prepared in advance")
    display_unit: str = ""
    display_icon: str = ""
    number_format: NumberFormat = NumberFormat()
    rank: int = 0

    @override
    def kind(self) -> str:
        return Says("자원 슬롯 유형", english="Resource slot type")

    @override
    def detail(self) -> str:
        parts = [Says(f"{self.slot_type.value} 유형", english=f"{self.slot_type.value} type")]
        if not self.enabled:
            parts.append(Says("사용하지 않음", english="unused"))
        return joined(parts)

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
            sealed_launch=False,
        )
