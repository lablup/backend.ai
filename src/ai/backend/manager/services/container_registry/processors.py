from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.processor.scope import ScopeActionProcessor
from ai.backend.manager.actions.processor.single_entity import SingleEntityActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.actions.validators import ActionValidators
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
from ai.backend.manager.services.container_registry.service import ContainerRegistryService


class ContainerRegistryProcessors(AbstractProcessorPackage):
    # Internal actions (no RBAC validators)
    rescan_images: ActionProcessor[RescanImagesAction, RescanImagesActionResult]
    clear_images: ActionProcessor[ClearImagesAction, ClearImagesActionResult]
    load_container_registries: ActionProcessor[
        LoadContainerRegistriesAction, LoadContainerRegistriesActionResult
    ]
    load_all_container_registries: ActionProcessor[
        LoadAllContainerRegistriesAction, LoadAllContainerRegistriesActionResult
    ]
    handle_harbor_webhook: ActionProcessor[
        HandleHarborWebhookAction, HandleHarborWebhookActionResult
    ]
    create_registry_quota: ActionProcessor[
        CreateRegistryQuotaAction, CreateRegistryQuotaActionResult
    ]
    read_registry_quota: ActionProcessor[ReadRegistryQuotaAction, ReadRegistryQuotaActionResult]
    update_registry_quota: ActionProcessor[
        UpdateRegistryQuotaAction, UpdateRegistryQuotaActionResult
    ]
    delete_registry_quota: ActionProcessor[
        DeleteRegistryQuotaAction, DeleteRegistryQuotaActionResult
    ]

    # Scope actions (with RBAC validators)
    get_container_registries: ScopeActionProcessor[
        GetContainerRegistriesAction, GetContainerRegistriesActionResult
    ]
    create_container_registry: ScopeActionProcessor[
        CreateContainerRegistryAction, CreateContainerRegistryActionResult
    ]
    search_container_registries: ScopeActionProcessor[
        SearchContainerRegistriesAction, SearchContainerRegistriesActionResult
    ]

    # Single-entity actions (with RBAC validators)
    modify_container_registry: SingleEntityActionProcessor[
        ModifyContainerRegistryAction, ModifyContainerRegistryActionResult
    ]
    delete_container_registry: SingleEntityActionProcessor[
        DeleteContainerRegistryAction, DeleteContainerRegistryActionResult
    ]

    def __init__(
        self,
        service: ContainerRegistryService,
        action_monitors: list[ActionMonitor],
        validators: ActionValidators,
    ) -> None:
        # Internal actions (no RBAC validators)
        self.rescan_images = ActionProcessor(service.rescan_images, action_monitors)
        self.clear_images = ActionProcessor(service.clear_images, action_monitors)
        self.load_container_registries = ActionProcessor(
            service.load_container_registries, action_monitors
        )
        self.load_all_container_registries = ActionProcessor(
            service.load_all_container_registries, action_monitors
        )
        self.handle_harbor_webhook = ActionProcessor(service.handle_harbor_webhook, action_monitors)
        self.create_registry_quota = ActionProcessor(service.create_registry_quota, action_monitors)
        self.read_registry_quota = ActionProcessor(service.read_registry_quota, action_monitors)
        self.update_registry_quota = ActionProcessor(service.update_registry_quota, action_monitors)
        self.delete_registry_quota = ActionProcessor(service.delete_registry_quota, action_monitors)

        # Scope actions (with RBAC validators)
        self.get_container_registries = ScopeActionProcessor(
            service.get_container_registries, action_monitors, validators=[validators.rbac.scope]
        )
        self.create_container_registry = ScopeActionProcessor(
            service.create_container_registry, action_monitors, validators=[validators.rbac.scope]
        )
        self.search_container_registries = ScopeActionProcessor(
            service.search_container_registries, action_monitors, validators=[validators.rbac.scope]
        )

        # Single-entity actions (with RBAC validators)
        self.modify_container_registry = SingleEntityActionProcessor(
            service.modify_container_registry,
            action_monitors,
            validators=[validators.rbac.single_entity],
        )
        self.delete_container_registry = SingleEntityActionProcessor(
            service.delete_container_registry,
            action_monitors,
            validators=[validators.rbac.single_entity],
        )

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            RescanImagesAction.spec(),
            ClearImagesAction.spec(),
            LoadContainerRegistriesAction.spec(),
            LoadAllContainerRegistriesAction.spec(),
            GetContainerRegistriesAction.spec(),
            CreateContainerRegistryAction.spec(),
            ModifyContainerRegistryAction.spec(),
            DeleteContainerRegistryAction.spec(),
            SearchContainerRegistriesAction.spec(),
            HandleHarborWebhookAction.spec(),
            CreateRegistryQuotaAction.spec(),
            ReadRegistryQuotaAction.spec(),
            UpdateRegistryQuotaAction.spec(),
            DeleteRegistryQuotaAction.spec(),
        ]
