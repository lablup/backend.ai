"""Write specs for an artifact."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import override

from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.common.data.entity.artifact import ArtifactID
from ai.backend.manager.data.artifact.types import (
    ArtifactData,
    ArtifactRevisionData,
    ArtifactStatus,
    ArtifactType,
)
from ai.backend.manager.models.artifact.creators import ArtifactCreator
from ai.backend.manager.models.artifact_revision.creators import ArtifactRevisionCreator
from ai.backend.testutils.scenario_steps import Says
from bai_scenario.seeds.seeder import (
    Naming,
    TestSeedFieldCreator,
    TestSeedRow,
)


@dataclass(frozen=True)
class TestSeedArtifact(TestSeedRow[ArtifactData]):
    """A model artifact a scan registered. The registry it names has no row of its own."""

    name_hint: str = "artifact"
    description: str | None = None
    readonly: bool = False
    registry_id: uuid.UUID = field(default_factory=uuid.uuid4)

    @override
    def kind(self) -> str:
        return Says("아티팩트", english="Artifact")

    @override
    def detail(self) -> str:
        return Says(
            "허깅 페이스 레지스트리에서 스캔한 모델",
            english="a model scanned from a HuggingFace registry",
        )

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
            readonly=self.readonly,
            description=self.description,
        )


@dataclass(frozen=True)
class TestSeedArtifactRevision(TestSeedFieldCreator[ArtifactData, ArtifactRevisionData]):
    """One revision of an artifact, in the state a presigned URL call reads."""

    version: str = "1.0"
    status: ArtifactStatus = ArtifactStatus.AVAILABLE

    @override
    def kind(self) -> str:
        return Says("아티팩트 리비전", english="artifact revision")

    @override
    def owner_id(self, owner: ArtifactData) -> ArtifactID:
        return ArtifactID(owner.id)

    @override
    def seed(self) -> ArtifactRevisionCreator:
        return ArtifactRevisionCreator(version=self.version, status=self.status)
