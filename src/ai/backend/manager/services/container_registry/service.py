from ai.backend.manager.container_registry import get_container_registry_cls
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
from ai.backend.manager.services.container_registry.actions.rescan_images import (
    RescanImagesAction,
    RescanImagesActionResult,
)


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

    async def rescan_images(self, action: RescanImagesAction) -> RescanImagesActionResult:
        registry_name = action.registry
        project = action.project

        registry_data = await self._container_registry_repository.get_by_registry_and_project(
            registry_name, project
        )

        registry_row = await self._container_registry_repository.get_registry_row_for_scanner(
            registry_name, project
        )

        scanner_cls = get_container_registry_cls(registry_row)
        scanner = scanner_cls(self._db, registry_name, registry_row)
        result = await scanner.rescan_single_registry(action.progress_reporter)

        return RescanImagesActionResult(
            images=result.images, errors=result.errors, registry=registry_data
        )

    async def clear_images(self, action: ClearImagesAction) -> ClearImagesActionResult:
        registry_data = await self._admin_container_registry_repository.clear_images_force(
            action.registry, action.project
        )

        return ClearImagesActionResult(registry=registry_data)

    async def load_container_registries(
        self, action: LoadContainerRegistriesAction
    ) -> LoadContainerRegistriesActionResult:
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
