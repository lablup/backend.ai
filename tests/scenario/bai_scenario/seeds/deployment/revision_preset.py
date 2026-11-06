"""Write specs for a deployment revision preset."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.common.config import PresetModelDefinition
from ai.backend.common.data.entity.deployment_preset import DeploymentPresetID
from ai.backend.common.data.entity.image import ImageID
from ai.backend.common.data.entity.runtime_variant import RuntimeVariantID
from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.common.types import ClusterMode
from ai.backend.manager.data.deployment_revision_preset.types import (
    DeploymentRevisionPresetData,
    ResourceSlotEntryData,
)
from ai.backend.manager.data.runtime_variant.types import RuntimeVariantData
from ai.backend.manager.models.deployment_revision_preset.creators import (
    DeploymentPresetCreator,
    PresetResourceSlotCreator,
)
from ai.backend.manager.models.runtime_variant_preset.types import RuntimeVariantPresetValueEntry
from ai.backend.testutils.scenario_steps import Says
from bai_scenario.seeds.seeder import Naming, TestSeedFieldCreator, TestSeedRowFrom, joined


@dataclass(frozen=True)
class TestSeedDeploymentRevisionPreset(
    TestSeedRowFrom[RuntimeVariantData, DeploymentRevisionPresetData]
):
    """A preset of the variant laid before it, on one node with one replica.

    The image is an id no row answers to: the preset table holds no reference to images.
    """

    name_hint: str = "preset"
    description: str | None = Says("미리 저장한 프리셋", english="a preset created in advance")
    image_id: UUID = UUID(int=7)
    model_definition: PresetModelDefinition | None = None
    preset_values: tuple[RuntimeVariantPresetValueEntry, ...] = ()

    @override
    def kind(self) -> str:
        return Says("배포 리비전 프리셋", english="Deployment revision preset")

    @override
    def detail(self) -> str:
        parts: list[Says] = [
            Says("단일 노드", english="single node"),
            Says("복제본 하나", english="one replica"),
            Says("롤링 업데이트", english="rolling update"),
        ]
        if self.model_definition is not None:
            parts.append(Says("모델 정의가 채워져 있다", english="carries a model definition"))
        if self.preset_values:
            parts.append(
                Says("런타임 파라미터 값이 채워져 있다", english="carries runtime preset values")
            )
        return joined(parts, ", ")

    @override
    def name(self, naming: Naming) -> str:
        return naming(self.name_hint)

    @override
    def seed(self, name: str, source: RuntimeVariantData) -> DeploymentPresetCreator:
        return DeploymentPresetCreator(
            runtime_variant_id=RuntimeVariantID(source.id),
            name=name,
            description=self.description,
            image_id=ImageID(self.image_id),
            model_definition=self.model_definition,
            resource_opts=[],
            cluster_mode=ClusterMode.SINGLE_NODE.value,
            cluster_size=1,
            startup_command=None,
            bootstrap_script=None,
            environ={},
            runtime_variant_preset_values=list(self.preset_values),
            replica_count=1,
            deployment_strategy=DeploymentStrategy.ROLLING,
            deployment_strategy_spec={},
        )


@dataclass(frozen=True)
class TestSeedPresetSlotOf(
    TestSeedFieldCreator[DeploymentRevisionPresetData, ResourceSlotEntryData]
):
    """One slot quantity the preset declares."""

    resource_type: str = "cpu"
    quantity: str = "4"

    @override
    def kind(self) -> str:
        return Says(
            f"{self.resource_type} 슬롯 하나를 두려 한다",
            english=f"declares one {self.resource_type} slot",
        )

    @override
    def owner_id(self, owner: DeploymentRevisionPresetData) -> DeploymentPresetID:
        return owner.id

    @override
    def seed(self) -> PresetResourceSlotCreator:
        return PresetResourceSlotCreator(
            entry=ResourceSlotEntryData(resource_type=self.resource_type, quantity=self.quantity)
        )
