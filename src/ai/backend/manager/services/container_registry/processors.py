from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
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
from ai.backend.manager.services.container_registry.service import ContainerRegistryService


class ContainerRegistryProcessors(AbstractProcessorPackage):
    rescan_images: ActionProcessor[RescanImagesAction, RescanImagesActionResult]
    clear_images: ActionProcessor[ClearImagesAction, ClearImagesActionResult]
    load_container_registries: ActionProcessor[
        LoadContainerRegistriesAction, LoadContainerRegistriesActionResult
    ]
    load_all_container_registries: ActionProcessor[
        LoadAllContainerRegistriesAction, LoadAllContainerRegistriesActionResult
    ]
    get_container_registries: ActionProcessor[
        GetContainerRegistriesAction, GetContainerRegistriesActionResult
    ]
    modify_container_registry: ActionProcessor[
        ModifyContainerRegistryAction, ModifyContainerRegistryActionResult
    ]
    delete_container_registry: ActionProcessor[
        DeleteContainerRegistryAction, DeleteContainerRegistryActionResult
    ]

    def __init__(
        self, service: ContainerRegistryService, action_monitors: list[ActionMonitor]
    ) -> None:
        self.rescan_images = ActionProcessor(service.rescan_images, action_monitors)
        self.clear_images = ActionProcessor(service.clear_images, action_monitors)
        self.load_container_registries = ActionProcessor(
            service.load_container_registries, action_monitors
        )
        self.load_all_container_registries = ActionProcessor(
            service.load_all_container_registries, action_monitors
        )
        self.get_container_registries = ActionProcessor(
            service.get_container_registries, action_monitors
        )
        self.modify_container_registry = ActionProcessor(
            service.modify_container_registry, action_monitors
        )
        self.delete_container_registry = ActionProcessor(
            service.delete_container_registry, action_monitors
        )

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            RescanImagesAction.spec(),
            ClearImagesAction.spec(),
            LoadContainerRegistriesAction.spec(),
            LoadAllContainerRegistriesAction.spec(),
            GetContainerRegistriesAction.spec(),
            ModifyContainerRegistryAction.spec(),
            DeleteContainerRegistryAction.spec(),
        ]
