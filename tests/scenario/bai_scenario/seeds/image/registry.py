"""Write specs for the container registry an image is scanned from."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from bai_scenario.seeds.seeder import Naming, SeedLink, SeedRow

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.models.container_registry.creators import (
    ContainerRegistryCreator,
    ContainerRegistryProjectCreator,
)


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


@dataclass(frozen=True)
class AllowProject(SeedLink[ProjectData, ContainerRegistryData]):
    """That project may reach the images of this registry."""

    @override
    def kind(self) -> str:
        return "가 이미지를 볼 수 있는"

    @override
    def scope_id(self, scope: ProjectData) -> ProjectID:
        return ProjectID(scope.id)

    @override
    def target_id(self, target: ContainerRegistryData) -> ContainerRegistryID:
        return ContainerRegistryID(target.id)

    @override
    def seed(self) -> ContainerRegistryProjectCreator:
        return ContainerRegistryProjectCreator()
