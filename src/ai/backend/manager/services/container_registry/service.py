from __future__ import annotations

import logging
import secrets
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.clients.container_registry.harbor import (
    AbstractPerProjectRegistryQuotaClient,
    HarborAuthArgs,
    HarborProjectInfo,
    PerProjectContainerRegistryQuotaClientPool,
)
from ai.backend.manager.container_registry import get_container_registry_cls
from ai.backend.manager.container_registry.harbor import HarborRegistry_v2
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.errors.image import (
    ContainerRegistryNotFound,
    ContainerRegistryWebhookAuthorizationFailed,
    HarborWebhookContainerRegistryRowNotFound,
)
from ai.backend.manager.models.container_registry.searchable_fields import (
    ContainerRegistrySearchableFields,
)
from ai.backend.manager.models.container_registry.updaters import ContainerRegistryGlobalUpdater
from ai.backend.manager.models.rbac import ProjectScope
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
from ai.backend.manager.services.container_registry.actions.read_registry_quota import (
    ReadRegistryQuotaAction,
    ReadRegistryQuotaActionResult,
)
from ai.backend.manager.services.container_registry.actions.rescan_images import (
    RescanImagesAction,
    RescanImagesActionResult,
)
from ai.backend.manager.services.container_registry.actions.set_container_registry_global import (
    SetContainerRegistryGlobalAction,
    SetContainerRegistryGlobalActionResult,
)
from ai.backend.manager.services.container_registry.actions.update_container_registry import (
    UpdateContainerRegistryAction,
    UpdateContainerRegistryActionResult,
)
from ai.backend.manager.services.container_registry.actions.update_registry_quota import (
    UpdateRegistryQuotaAction,
    UpdateRegistryQuotaActionResult,
)

if TYPE_CHECKING:
    from ai.backend.manager.models.container_registry import ContainerRegistryRow

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass(frozen=True)
class _RegistryQuotaTarget:
    client: AbstractPerProjectRegistryQuotaClient
    project: HarborProjectInfo
    auth: HarborAuthArgs


class ContainerRegistryService:
    _db: ExtendedAsyncSAEngine
    _container_registry_repository: ContainerRegistryRepository
    _quota_client_pool: PerProjectContainerRegistryQuotaClientPool

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
        container_registry_repository: ContainerRegistryRepository,
        quota_client_pool: PerProjectContainerRegistryQuotaClientPool,
    ) -> None:
        self._db = db
        self._container_registry_repository = container_registry_repository
        self._quota_client_pool = quota_client_pool

    async def create_container_registry(
        self, action: CreateContainerRegistryAction
    ) -> CreateContainerRegistryActionResult:
        data = await self._container_registry_repository.create_registry(action.creator)
        return CreateContainerRegistryActionResult(data=data)

    async def update_container_registry(
        self, action: UpdateContainerRegistryAction
    ) -> UpdateContainerRegistryActionResult:
        data = await self._container_registry_repository.modify_registry(action.updater)
        return UpdateContainerRegistryActionResult(data=data)

    async def set_container_registry_global(
        self, action: SetContainerRegistryGlobalAction
    ) -> SetContainerRegistryGlobalActionResult:
        data = await self._container_registry_repository.set_global(
            ContainerRegistryGlobalUpdater(
                registry_id=action.registry_id, is_global=action.is_global
            )
        )
        return SetContainerRegistryGlobalActionResult(data=data)

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
            images=result.images,
            errors=result.errors,
            registry=ContainerRegistrySearchableFields.own.to_data(registry_row),
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

            # Validate webhook authorization: if the registry configured a secret,
            # the request MUST present a matching header (omitting it must fail).
            expected_auth = (registry_row.extra or {}).get("webhook_auth_header")
            if expected_auth:
                if not action.auth_header or not secrets.compare_digest(
                    action.auth_header.encode(), expected_auth.encode()
                ):
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

    async def _registry_quota_target(self, scope_id: ProjectScope) -> _RegistryQuotaTarget:
        registry_info = await self._container_registry_repository.get_by_project_scope(scope_id)
        return _RegistryQuotaTarget(
            client=self._quota_client_pool.make_client(registry_info.type),
            project=HarborProjectInfo(
                url=registry_info.url,
                project=registry_info.project,
                ssl_verify=registry_info.ssl_verify,
            ),
            auth=HarborAuthArgs(username=registry_info.username, password=registry_info.password),
        )

    async def create_registry_quota(
        self, action: CreateRegistryQuotaAction
    ) -> CreateRegistryQuotaActionResult:
        target = await self._registry_quota_target(action.scope_id)
        await target.client.create_quota(target.project, action.quota, target.auth)
        return CreateRegistryQuotaActionResult()

    async def read_registry_quota(
        self, action: ReadRegistryQuotaAction
    ) -> ReadRegistryQuotaActionResult:
        target = await self._registry_quota_target(action.scope_id)
        quota = await target.client.read_quota(target.project, target.auth)
        return ReadRegistryQuotaActionResult(quota=quota)

    async def update_registry_quota(
        self, action: UpdateRegistryQuotaAction
    ) -> UpdateRegistryQuotaActionResult:
        target = await self._registry_quota_target(action.scope_id)
        await target.client.update_quota(target.project, action.quota, target.auth)
        return UpdateRegistryQuotaActionResult()

    async def delete_registry_quota(
        self, action: DeleteRegistryQuotaAction
    ) -> DeleteRegistryQuotaActionResult:
        target = await self._registry_quota_target(action.scope_id)
        await target.client.delete_quota(target.project, target.auth)
        return DeleteRegistryQuotaActionResult()
