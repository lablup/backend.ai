from typing import Optional

from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

from .repository import ContainerRegistryRepository


class AdminContainerRegistryRepository:
    _repository: ContainerRegistryRepository

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._repository = ContainerRegistryRepository(db)

    async def clear_images_force(
        self,
        registry_name: str,
        project: Optional[str] = None,
    ) -> ContainerRegistryData:
        """
        Forcefully clear images from a container registry without any validation.
        This is an admin-only operation that should be used with caution.
        """
        return await self._repository.clear_images(registry_name, project)

    async def get_by_registry_and_project_force(
        self,
        registry_name: str,
        project: Optional[str] = None,
    ) -> ContainerRegistryData:
        """
        Forcefully get container registry by name and project without any validation.
        This is an admin-only operation that should be used with caution.
        """
        return await self._repository.get_by_registry_and_project(registry_name, project)

    async def get_by_registry_name_force(self, registry_name: str) -> list[ContainerRegistryData]:
        """
        Forcefully get container registries by name without any validation.
        This is an admin-only operation that should be used with caution.
        """
        return await self._repository.get_by_registry_name(registry_name)

    async def get_all_force(self) -> list[ContainerRegistryData]:
        """
        Forcefully get all container registries without any validation.
        This is an admin-only operation that should be used with caution.
        """
        return await self._repository.get_all()
