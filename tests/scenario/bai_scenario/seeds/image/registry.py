"""Write specs for the container registry an image is scanned from."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.models.container_registry.creators import ContainerRegistryCreator
from bai_scenario.seeds.seeder import Naming, SeedRow


@dataclass(frozen=True)
class SeedContainerRegistry(SeedRow[ContainerRegistryData]):
    """A registry. An image joins the one it came from, so it is laid first."""

    name_hint: str = "registry"

    @override
    def kind(self) -> str:
        return "컨테이너 레지스트리"

    @override
    def detail(self) -> str:
        return "이미지를 가져오는 곳"

    @override
    def name(self, naming: Naming) -> str:
        return naming(self.name_hint)

    @override
    def seed(self, name: str) -> ContainerRegistryCreator:
        return ContainerRegistryCreator(
            url=f"https://{name}.scenario.local",
            type=ContainerRegistryType.DOCKER,
            registry_name=name,
        )
