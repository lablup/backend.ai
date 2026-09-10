"""Write specs for an image."""

from __future__ import annotations

from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.data.image.types import ImageData, ImageType
from ai.backend.manager.models.image.creators import ImageCreator
from bai_scenario.seeds.seeder import SpecFrom


def seed_image(
    *, name_hint: str = "image", architecture: str = "x86_64"
) -> SpecFrom[ContainerRegistryData, ImageData]:
    """An image of the given registry. A session names one to run."""

    def build(name: str, registry: ContainerRegistryData) -> ImageCreator:
        return ImageCreator(
            name=name,
            project=None,
            architecture=architecture,
            registry_id=ContainerRegistryID(registry.id),
            registry=registry.registry_name,
            image=name,
            tag="latest",
            config_digest=f"sha256:{name:>064}".replace(" ", "0"),
            size_bytes=0,
            labels={},
            type=ImageType.COMPUTE,
        )

    return SpecFrom("an image", name_hint, build)
