from typing import TYPE_CHECKING

from ai.backend.manager.container_registry import get_container_registry_cls
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.errors.image import ContainerRegistryNotFound
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.container_registry.admin_repository import (
    AdminContainerRegistryRepository,
)
from ai.backend.manager.repositories.container_registry.repository import (
    ContainerRegistryRepository,
)
from ai.backend.manager.services.container_registry.actions.clear_images import (
    ClearImagesAction,
    ClearImagesActionResult,
)
from ai.backend.manager.services.container_registry.actions.delete_container_registry import (
    DeleteContainerRegistryAction,
    DeleteContainerRegistryActionResult,
)
from ai.backend.manager.services.container_registry.actions.get_container_registries import (
    GetContainerRegistriesAction,
    GetContainerRegistriesActionResult,
)
from ai.backend.manager.services.container_registry.actions.load_all_container_registries import (
    LoadAllContainerRegistriesAction,
    LoadAllContainerRegistriesActionResult,
)
from ai.backend.manager.services.container_registry.actions.load_container_registries import (
    LoadContainerRegistriesAction,
    LoadContainerRegistriesActionResult,
)
from ai.backend.manager.services.container_registry.actions.modify_container_registry import (
    ModifyContainerRegistryAction,
    ModifyContainerRegistryActionResult,
)
from ai.backend.manager.services.container_registry.actions.rescan_images import (
    RescanImagesAction,
    RescanImagesActionResult,
)

if TYPE_CHECKING:
    from ai.backend.manager.models.container_registry import ContainerRegistryRow


class ContainerRegistryService:
    _db: ExtendedAsyncSAEngine
    _container_registry_repository: ContainerRegistryRepository
    _admin_container_registry_repository: AdminContainerRegistryRepository

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
        container_registry_repository: ContainerRegistryRepository,
        admin_container_registry_repository: AdminContainerRegistryRepository,
    ) -> None:
        self._db = db
        self._container_registry_repository = container_registry_repository
        self._admin_container_registry_repository = admin_container_registry_repository

    async def modify_container_registry(
        self, action: ModifyContainerRegistryAction
    ) -> ModifyContainerRegistryActionResult:
        data = await self._container_registry_repository.modify_registry(action.updater)
        return ModifyContainerRegistryActionResult(data=data)

    async def delete_container_registry(
        self, action: DeleteContainerRegistryAction
    ) -> DeleteContainerRegistryActionResult:
        data = await self._container_registry_repository.delete_registry(action.purger)
        return DeleteContainerRegistryActionResult(data=data)

    async def rescan_images(self, action: RescanImagesAction) -> RescanImagesActionResult:
        registry_name = action.registry
        project = action.project

        registry_row: ContainerRegistryRow = (
            await self._container_registry_repository.get_registry_row_for_scanner(
                registry_name, project
            )
        )

        scanner_cls = get_container_registry_cls(registry_row)
        scanner = scanner_cls(self._db, registry_name, registry_row)
        result = await scanner.rescan_single_registry(action.progress_reporter)

        return RescanImagesActionResult(
            images=result.images, errors=result.errors, registry=registry_row.to_dataclass()
        )

    async def clear_images(self, action: ClearImagesAction) -> ClearImagesActionResult:
        registry_data = await self._admin_container_registry_repository.clear_images_force(
            action.registry, action.project
        )

        return ClearImagesActionResult(registry=registry_data)

    async def load_container_registries(
        self, action: LoadContainerRegistriesAction
    ) -> LoadContainerRegistriesActionResult:
        registries: list[ContainerRegistryData] = []
        if action.project is not None:
            try:
                registry_data = (
                    await self._container_registry_repository.get_by_registry_and_project(
                        action.registry, action.project
                    )
                )
                registries = [registry_data]
            except ContainerRegistryNotFound:
                registries = []
        else:
            registries = await self._container_registry_repository.get_by_registry_name(
                action.registry
            )

        return LoadContainerRegistriesActionResult(registries=registries)

    async def load_all_container_registries(
        self, _action: LoadAllContainerRegistriesAction
    ) -> LoadAllContainerRegistriesActionResult:
        registries = await self._container_registry_repository.get_all()
        return LoadAllContainerRegistriesActionResult(registries=registries)

    async def get_container_registries(
        self, _action: GetContainerRegistriesAction
    ) -> GetContainerRegistriesActionResult:
        registries = await self._container_registry_repository.get_known_registries()
        return GetContainerRegistriesActionResult(registries=registries)
