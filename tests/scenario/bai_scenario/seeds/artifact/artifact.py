"""Write specs for an artifact."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import override

from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.manager.data.artifact.types import ArtifactData, ArtifactType
from ai.backend.manager.models.artifact.creators import ArtifactCreator
from bai_scenario.seeds.seeder import Naming, TestSeedRow


@dataclass(frozen=True)
class TestSeedArtifact(TestSeedRow[ArtifactData]):
    """A model artifact a scan registered. The registry it names has no row of its own."""

    name_hint: str = "artifact"
    description: str | None = None
    registry_id: uuid.UUID = field(default_factory=uuid.uuid4)

    @override
    def kind(self) -> str:
        return "아티팩트"

    @override
    def detail(self) -> str:
        return "HuggingFace 레지스트리에서 스캔된 모델"

    @override
    def name(self, naming: Naming) -> str:
        return naming(self.name_hint)

    @override
    def seed(self, name: str) -> ArtifactCreator:
        return ArtifactCreator(
            name=name,
            type=ArtifactType.MODEL,
            registry_id=self.registry_id,
            registry_type=ArtifactRegistryType.HUGGINGFACE,
            source_registry_id=self.registry_id,
            source_registry_type=ArtifactRegistryType.HUGGINGFACE,
            readonly=False,
            description=self.description,
        )
