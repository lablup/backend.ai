"""Write specs for a deployment revision preset and the slots it allocates.

A preset is laid under a runtime variant, names an image, and is created in the public
scope. What it allocates is a field row per slot, laid under the preset.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import override

from ai.backend.common.data.entity.deployment_preset import DeploymentPresetID
from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.manager.data.deployment_revision_preset.types import (
    DeploymentRevisionPresetData,
    ResourceSlotEntryData,
)
from ai.backend.manager.data.image.types import ImageData
from ai.backend.manager.data.runtime_variant.types import RuntimeVariantData
from ai.backend.manager.models.deployment_revision_preset.creators import (
    DeploymentPresetCreator,
    PresetResourceSlotCreator,
)
from bai_scenario.seeds.seeder import Naming, SeedField, SeedRowFromTwo


@dataclass(frozen=True)
class SeedDeploymentPreset(
    SeedRowFromTwo[RuntimeVariantData, ImageData, DeploymentRevisionPresetData]
):
    """A preset of the given variant that runs the given image."""

    name_hint: str = "preset"

    @override
    def kind(self) -> str:
        return "배포 리비전 프리셋"

    @override
    def detail(self) -> str:
        return "공개 스코프에 놓이고, 할당 슬롯은 따로 심는다"

    @override
    def name(self, naming: Naming) -> str:
        return naming(self.name_hint)

    @override
    def seed(
        self, name: str, first: RuntimeVariantData, second: ImageData
    ) -> DeploymentPresetCreator:
        return DeploymentPresetCreator(
            runtime_variant_id=first.id,
            name=name,
            description=None,
            image_id=second.id,
            model_definition=None,
            resource_opts=[],
            cluster_mode="single-node",
            cluster_size=1,
            startup_command=None,
            bootstrap_script=None,
            environ={},
            runtime_variant_preset_values=[],
            replica_count=1,
            deployment_strategy=DeploymentStrategy.ROLLING,
            deployment_strategy_spec={},
        )


@dataclass(frozen=True)
class SeedPresetSlot(SeedField[DeploymentRevisionPresetData, ResourceSlotEntryData]):
    """How much of one slot the preset allocates."""

    slot: str
    quantity: Decimal

    @override
    def kind(self) -> str:
        return f"{self.slot} {self.quantity} 할당"

    @override
    def owner_id(self, owner: DeploymentRevisionPresetData) -> DeploymentPresetID:
        return DeploymentPresetID(owner.id)

    @override
    def seed(self) -> PresetResourceSlotCreator:
        return PresetResourceSlotCreator(
            entry=ResourceSlotEntryData(resource_type=self.slot, quantity=str(self.quantity))
        )
