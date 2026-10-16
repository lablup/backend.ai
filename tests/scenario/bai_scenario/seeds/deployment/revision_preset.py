"""Write specs for a deployment revision preset."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.common.data.entity.image import ImageID
from ai.backend.common.data.entity.runtime_variant import RuntimeVariantID
from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.common.types import ClusterMode
from ai.backend.manager.data.deployment_revision_preset.types import DeploymentRevisionPresetData
from ai.backend.manager.data.runtime_variant.types import RuntimeVariantData
from ai.backend.manager.models.deployment_revision_preset.creators import DeploymentPresetCreator
from bai_scenario.seeds.seeder import Naming, TestSeedRowFrom


@dataclass(frozen=True)
class TestSeedDeploymentRevisionPreset(
    TestSeedRowFrom[RuntimeVariantData, DeploymentRevisionPresetData]
):
    """A preset of the variant laid before it, on one node with one replica.

    The image is an id no row answers to: the preset table holds no reference to images.
    """

    name_hint: str = "preset"
    description: str | None = "미리 만들어 둔 프리셋"
    image_id: UUID = UUID(int=7)

    @override
    def kind(self) -> str:
        return "배포 리비전 프리셋"

    @override
    def detail(self) -> str:
        return "단일 노드, 레플리카 하나, 롤링 업데이트"

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
            model_definition=None,
            resource_opts=[],
            cluster_mode=ClusterMode.SINGLE_NODE.value,
            cluster_size=1,
            startup_command=None,
            bootstrap_script=None,
            environ={},
            runtime_variant_preset_values=[],
            replica_count=1,
            deployment_strategy=DeploymentStrategy.ROLLING,
            deployment_strategy_spec={},
        )
