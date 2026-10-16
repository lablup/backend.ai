"""Write specs for the HuggingFace and Reservoir registries."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.manager.data.huggingface_registry.types import HuggingFaceRegistryData
from ai.backend.manager.data.reservoir_registry.types import ReservoirRegistryData
from ai.backend.manager.models.artifact_registries.creators import ArtifactRegistryMetaCreator
from ai.backend.manager.models.huggingface_registry.creators import HuggingFaceRegistryCreator
from ai.backend.manager.models.reservoir_registry.creators import ReservoirRegistryCreator
from bai_scenario.seeds.seeder import Naming, TestSeedRegistryPair, TestSeedRow


@dataclass(frozen=True)
class TestSeedHuggingFaceRegistry(TestSeedRow[HuggingFaceRegistryData]):
    """A HuggingFace registry and the row naming it."""

    name_hint: str = "huggingface"
    url: str = "https://huggingface.co"
    token: str | None = None

    @override
    def kind(self) -> str:
        return "HuggingFace 레지스트리"

    @override
    def detail(self) -> str:
        return f"{self.url} 을 가리킨다"

    @override
    def name(self, naming: Naming) -> str:
        return naming(self.name_hint)

    @override
    def seed(self, name: str) -> TestSeedRegistryPair[HuggingFaceRegistryData]:
        return TestSeedRegistryPair(
            creator=HuggingFaceRegistryCreator(url=self.url, token=self.token),
            meta=ArtifactRegistryMetaCreator(name=name, type=ArtifactRegistryType.HUGGINGFACE),
        )


@dataclass(frozen=True)
class TestSeedReservoirRegistry(TestSeedRow[ReservoirRegistryData]):
    """A Reservoir registry and the row naming it."""

    name_hint: str = "reservoir"
    endpoint: str = "https://reservoir.example.com"
    access_key: str = "access-key"
    secret_key: str = "secret-key"
    api_version: str = "v1"

    @override
    def kind(self) -> str:
        return "Reservoir 레지스트리"

    @override
    def detail(self) -> str:
        return f"{self.endpoint} 을 가리킨다"

    @override
    def name(self, naming: Naming) -> str:
        return naming(self.name_hint)

    @override
    def seed(self, name: str) -> TestSeedRegistryPair[ReservoirRegistryData]:
        return TestSeedRegistryPair(
            creator=ReservoirRegistryCreator(
                endpoint=self.endpoint,
                access_key=self.access_key,
                secret_key=self.secret_key,
                api_version=self.api_version,
            ),
            meta=ArtifactRegistryMetaCreator(name=name, type=ArtifactRegistryType.RESERVOIR),
        )
