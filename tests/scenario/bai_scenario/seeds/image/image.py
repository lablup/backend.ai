"""Write specs for an image."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.data.image.types import ImageData, ImageType
from ai.backend.manager.models.image.creators import ImageCreator
from bai_scenario.seeds.seeder import Naming, SeedRowFrom


@dataclass(frozen=True)
class SeedImage(SeedRowFrom[ContainerRegistryData, ImageData]):
    """An image of the given registry. A session names one to run."""

    name_hint: str = "image"
    architecture: str = "x86_64"

    @override
    def kind(self) -> str:
        return "이미지"

    @override
    def detail(self) -> str:
        return f"{self.architecture} 이미지"

    @override
    def name(self, naming: Naming) -> str:
        return naming(self.name_hint)

    @override
    def seed(self, name: str, source: ContainerRegistryData) -> ImageCreator:
        return ImageCreator(
            name=name,
            project=None,
            architecture=self.architecture,
            registry_id=ContainerRegistryID(source.id),
            registry=source.registry_name,
            image=name,
            tag="latest",
            config_digest=f"sha256:{name:>064}".replace(" ", "0"),
            size_bytes=0,
            labels={},
            type=ImageType.COMPUTE,
        )
