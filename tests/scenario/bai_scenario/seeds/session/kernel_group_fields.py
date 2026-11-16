"""Write specs for the environ and resource slot rows of a kernel group."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import override

from ai.backend.common.data.entity.kernel_group import KernelGroupID
from ai.backend.common.data.entity.resource_slot import ResourceSlotName
from ai.backend.manager.data.kernel_group.types import (
    KernelGroupData,
    KernelGroupEnvironData,
    KernelGroupResourceSlotData,
)
from ai.backend.manager.models.kernel_group_environ.creators import KernelGroupEnvironCreator
from ai.backend.manager.models.kernel_group_resource_slot.creators import (
    KernelGroupResourceSlotCreator,
)
from ai.backend.testutils.scenario_steps import Says
from bai_scenario.seeds.seeder import TestSeedNestedFieldCreator


@dataclass(frozen=True)
class TestSeedKernelGroupEnvironOf(
    TestSeedNestedFieldCreator[KernelGroupData, KernelGroupEnvironData]
):
    """One environment variable of the given kernel group."""

    key: str
    value: str

    @override
    def kind(self) -> str:
        return Says("환경 변수 하나를 갖습니다", english="has one environment variable")

    @override
    def owner_id(self, owner: KernelGroupData) -> KernelGroupID:
        return KernelGroupID(owner.id)

    @override
    def seed(self) -> KernelGroupEnvironCreator:
        return KernelGroupEnvironCreator(key=self.key, value=self.value)


@dataclass(frozen=True)
class TestSeedKernelGroupResourceSlotOf(
    TestSeedNestedFieldCreator[KernelGroupData, KernelGroupResourceSlotData]
):
    """What the given kernel group asks for in one slot, on each of its kernels."""

    slot_name: str
    quantity: Decimal

    @override
    def kind(self) -> str:
        return Says(
            f"{self.slot_name} 슬롯 요구량 하나를 갖습니다",
            english=f"asks for {self.quantity} in the {self.slot_name} slot",
        )

    @override
    def owner_id(self, owner: KernelGroupData) -> KernelGroupID:
        return KernelGroupID(owner.id)

    @override
    def seed(self) -> KernelGroupResourceSlotCreator:
        return KernelGroupResourceSlotCreator(
            slot_name=ResourceSlotName(self.slot_name), quantity=self.quantity
        )
