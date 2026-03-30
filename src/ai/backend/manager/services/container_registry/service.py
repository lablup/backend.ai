from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Final

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.container_registry import get_container_registry_cls
from ai.backend.manager.container_registry.harbor import HarborRegistry_v2
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.errors.image import (
    ContainerRegistryNotFound,
    ContainerRegistryWebhookAuthorizationFailed,
    HarborWebhookContainerRegistryRowNotFound,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.container_registry.repository import (
    ContainerRegistryRepository,
)
from ai.backend.manager.services.container_registry.actions.clear_images import (
    ClearImagesAction,
    ClearImagesActionResult,
)
from ai.backend.manager.services.container_registry.actions.create_container_registry import (
    CreateContainerRegistryAction,
    CreateContainerRegistryActionResult,
)
from ai.backend.manager.services.container_registry.actions.create_registry_quota import (
    CreateRegistryQuotaAction,
    CreateRegistryQuotaActionResult,
)
from ai.backend.manager.services.container_registry.actions.delete_container_registry import (
    DeleteContainerRegistryAction,
    DeleteContainerRegistryActionResult,
)
from ai.backend.manager.services.container_registry.actions.delete_registry_quota import (
    DeleteRegistryQuotaAction,
    DeleteRegistryQuotaActionResult,
)
from ai.backend.manager.services.container_registry.actions.get_container_registries import (
    GetContainerRegistriesAction,
    GetContainerRegistriesActionResult,
)
from ai.backend.manager.services.container_registry.actions.handle_harbor_webhook import (
    HandleHarborWebhookAction,
    HandleHarborWebhookActionResult,
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
from ai.backend.manager.services.container_registry.actions.read_registry_quota import (
    ReadRegistryQuotaAction,
    ReadRegistryQuotaActionResult,
)
from ai.backend.manager.services.container_registry.actions.rescan_images import (
    RescanImagesAction,
    RescanImagesActionResult,
)
from ai.backend.manager.services.container_registry.actions.search_container_registries import (
    SearchContainerRegistriesAction,
    SearchContainerRegistriesActionResult,
)
from ai.backend.manager.services.container_registry.actions.update_registry_quota import (
    UpdateRegistryQuotaAction,
    UpdateRegistryQuotaActionResult,
)

if TYPE_CHECKING:
    from ai.backend.manager.models.container_registry import ContainerRegistryRow
    from ai.backend.manager.service.container_registry.harbor import (
        AbstractPerProjectContainerRegistryQuotaService,
    )

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ContainerRegistryService:
    _db: ExtendedAsyncSAEngine
    _container_registry_repository: ContainerRegistryRepository
    _quota_service: AbstractPerProjectContainerRegistryQuotaService | None

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
        container_registry_repository: ContainerRegistryRepository,
        quota_service: AbstractPerProjectContainerRegistryQuotaService | None = None,
    ) -> None:
        self._db = db
        self._container_registry_repository = container_registry_repository
        self._quota_service = quota_service

    async def create_container_registry(
        self, action: CreateContainerRegistryAction
    ) -> CreateContainerRegistryActionResult:
        data = await self._container_registry_repository.create_registry(action.creator)
        return CreateContainerRegistryActionResult(data=data)

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
        registry_data = await self._container_registry_repository.clear_images(
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

    async def search_container_registries(
        self, action: SearchContainerRegistriesAction
    ) -> SearchContainerRegistriesActionResult:
        """Search container registries with pagination and ordering."""
        result = await self._container_registry_repository.search_container_registries(
            action.querier
        )
        return SearchContainerRegistriesActionResult(
            data=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def get_container_registries(
        self, _action: GetContainerRegistriesAction
    ) -> GetContainerRegistriesActionResult:
        registries = await self._container_registry_repository.get_known_registries()
        return GetContainerRegistriesActionResult(registries=registries)

    async def handle_harbor_webhook(
        self, action: HandleHarborWebhookAction
    ) -> HandleHarborWebhookActionResult:
        """Handle a Harbor container registry webhook event."""
        for resource in action.resources:
            registry_url = resource.resource_url.split("/")[0]
            registry_row = (
                await self._container_registry_repository.get_registry_by_url_and_project(
                    registry_url, action.project
                )
            )
            if not registry_row:
                raise HarborWebhookContainerRegistryRowNotFound(
                    extra_msg=(
                        f"Harbor webhook triggered, but the matching container registry"
                        f" row not found! (registry_url: {registry_url},"
                        f" project: {action.project})"
                    ),
                )

            # Validate webhook authorization
            if action.auth_header:
                extra = registry_row.extra or {}
                if extra.get("webhook_auth_header") != action.auth_header:
                    raise ContainerRegistryWebhookAuthorizationFailed(
                        extra_msg=(
                            f"Unauthorized webhook request"
                            f" (registry: {registry_row.registry_name},"
                            f" project: {action.project})"
                        ),
                    )

            # Handle event by type
            if action.event_type == "PUSH_ARTIFACT":
                scanner = HarborRegistry_v2(self._db, registry_row.registry_name, registry_row)
                await scanner.scan_single_ref(f"{action.project}/{action.img_name}:{resource.tag}")
            else:
                log.debug(
                    'Ignore harbor webhook event: "{}". Recommended to modify the'
                    " webhook config to not subscribe to this event type.",
                    action.event_type,
                )

        return HandleHarborWebhookActionResult()

    def _ensure_quota_service(self) -> AbstractPerProjectContainerRegistryQuotaService:
        if self._quota_service is None:
            raise RuntimeError("Registry quota service is not configured")
        return self._quota_service

    async def create_registry_quota(
        self, action: CreateRegistryQuotaAction
    ) -> CreateRegistryQuotaActionResult:
        quota_service = self._ensure_quota_service()
        await quota_service.create_quota(action.scope_id, action.quota)
        return CreateRegistryQuotaActionResult()

    async def read_registry_quota(
        self, action: ReadRegistryQuotaAction
    ) -> ReadRegistryQuotaActionResult:
        quota_service = self._ensure_quota_service()
        quota = await quota_service.read_quota(action.scope_id)
        return ReadRegistryQuotaActionResult(quota=quota)

    async def update_registry_quota(
        self, action: UpdateRegistryQuotaAction
    ) -> UpdateRegistryQuotaActionResult:
        quota_service = self._ensure_quota_service()
        await quota_service.update_quota(action.scope_id, action.quota)
        return UpdateRegistryQuotaActionResult()

    async def delete_registry_quota(
        self, action: DeleteRegistryQuotaAction
    ) -> DeleteRegistryQuotaActionResult:
        quota_service = self._ensure_quota_service()
        await quota_service.delete_quota(action.scope_id)
        return DeleteRegistryQuotaActionResult()
