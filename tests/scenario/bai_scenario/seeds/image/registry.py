"""Write specs for the container registry an image is scanned from."""

from __future__ import annotations

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.models.container_registry.creators import ContainerRegistryCreator
from bai_scenario.seeds.seeder import Spec


def seed_container_registry(*, name_hint: str = "registry") -> Spec[ContainerRegistryData]:
    """A registry. An image joins the one it came from, so it is laid first."""

    def build(name: str) -> ContainerRegistryCreator:
        return ContainerRegistryCreator(
            url=f"https://{name}.scenario.local",
            type=ContainerRegistryType.DOCKER,
            registry_name=name,
        )

    return Spec("a container registry", name_hint, build)
