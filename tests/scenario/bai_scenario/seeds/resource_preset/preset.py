"""Write specs for a resource preset."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import override

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.resource_preset.types import ResourcePresetData
from ai.backend.manager.models.resource_preset.creators import ResourcePresetCreator
from ai.backend.testutils.scenario_steps import Says
from bai_scenario.seeds.seeder import Naming, TestSeedRow

SLOTS = ResourceSlot({"cpu": Decimal("1"), "mem": Decimal("1073741824")})
"""The intrinsic slots every preset must carry."""


@dataclass(frozen=True)
class TestSeedResourcePreset(TestSeedRow[ResourcePresetData]):
    """A resource preset bound to no resource group, so it sits in public."""

    name_hint: str = "preset"

    @override
    def kind(self) -> str:
        return Says("자원 프리셋", english="Resource preset")

    @override
    def detail(self) -> str:
        return Says(
            "자원 그룹에 묶이지 않아 public 에 속합니다",
            english="belongs to public because it is bound to no resource group",
        )

    @override
    def name(self, naming: Naming) -> str:
        return naming(self.name_hint)

    @override
    def seed(self, name: str) -> ResourcePresetCreator:
        return ResourcePresetCreator(
            name=name,
            resource_slots=SLOTS,
            shared_memory=None,
            resource_group_name=None,
        )
