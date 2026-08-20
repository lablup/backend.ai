from typing import Any

from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
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
from ai.backend.manager.services.container_registry.actions.search_container_registries import (
    SearchContainerRegistriesAction,
    SearchContainerRegistriesActionResult,
)
from ai.backend.manager.services.container_registry.actions.update_container_registry import (
    UpdateContainerRegistryAction,
    UpdateContainerRegistryActionResult,
)
from ai.backend.manager.services.container_registry.actions.update_registry_quota import (
    UpdateRegistryQuotaAction,
    UpdateRegistryQuotaActionResult,
)
from ai.backend.manager.services.container_registry.service import ContainerRegistryService


class ContainerRegistryProcessors:
    rescan_images: GlobalActionProcessor[RescanImagesAction, RescanImagesActionResult]
    clear_images: GlobalActionProcessor[ClearImagesAction, ClearImagesActionResult]
    load_container_registries: GlobalActionProcessor[
        LoadContainerRegistriesAction, LoadContainerRegistriesActionResult
    ]
    load_all_container_registries: GlobalActionProcessor[
        LoadAllContainerRegistriesAction, LoadAllContainerRegistriesActionResult
    ]
    get_container_registries: GlobalActionProcessor[
        GetContainerRegistriesAction, GetContainerRegistriesActionResult
    ]
    create_container_registry: GlobalActionProcessor[
        CreateContainerRegistryAction, CreateContainerRegistryActionResult
    ]
    update_container_registry: GlobalActionProcessor[
        UpdateContainerRegistryAction, UpdateContainerRegistryActionResult
    ]
    delete_container_registry: GlobalActionProcessor[
        DeleteContainerRegistryAction, DeleteContainerRegistryActionResult
    ]
    search_container_registries: GlobalActionProcessor[
        SearchContainerRegistriesAction, SearchContainerRegistriesActionResult
    ]
    handle_harbor_webhook: GlobalActionProcessor[
        HandleHarborWebhookAction, HandleHarborWebhookActionResult
    ]
    create_registry_quota: GlobalActionProcessor[
        CreateRegistryQuotaAction, CreateRegistryQuotaActionResult
    ]
    read_registry_quota: GlobalActionProcessor[
        ReadRegistryQuotaAction, ReadRegistryQuotaActionResult
    ]
    update_registry_quota: GlobalActionProcessor[
        UpdateRegistryQuotaAction, UpdateRegistryQuotaActionResult
    ]
    delete_registry_quota: GlobalActionProcessor[
        DeleteRegistryQuotaAction, DeleteRegistryQuotaActionResult
    ]

    def __init__(self, group: ProcessorGroup[Any], service: ContainerRegistryService) -> None:
        self.rescan_images = group.global_scope(RescanImagesAction, service.rescan_images)
        self.clear_images = group.global_scope(ClearImagesAction, service.clear_images)
        self.load_container_registries = group.global_scope(
            LoadContainerRegistriesAction, service.load_container_registries
        )
        self.load_all_container_registries = group.global_scope(
            LoadAllContainerRegistriesAction, service.load_all_container_registries
        )
        self.get_container_registries = group.global_scope(
            GetContainerRegistriesAction, service.get_container_registries
        )
        self.create_container_registry = group.global_scope(
            CreateContainerRegistryAction, service.create_container_registry
        )
        self.update_container_registry = group.global_scope(
            UpdateContainerRegistryAction, service.update_container_registry
        )
        self.delete_container_registry = group.global_scope(
            DeleteContainerRegistryAction, service.delete_container_registry
        )
        self.search_container_registries = group.global_scope(
            SearchContainerRegistriesAction, service.search_container_registries
        )
        self.handle_harbor_webhook = group.global_scope(
            HandleHarborWebhookAction, service.handle_harbor_webhook
        )
        self.create_registry_quota = group.global_scope(
            CreateRegistryQuotaAction, service.create_registry_quota
        )
        self.read_registry_quota = group.global_scope(
            ReadRegistryQuotaAction, service.read_registry_quota
        )
        self.update_registry_quota = group.global_scope(
            UpdateRegistryQuotaAction, service.update_registry_quota
        )
        self.delete_registry_quota = group.global_scope(
            DeleteRegistryQuotaAction, service.delete_registry_quota
        )
