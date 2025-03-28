from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.services.container_registry.actions.get_container_registries import (
    GetContainerRegistriesAction,
    GetContainerRegistriesActionResult,
)
from ai.backend.manager.services.container_registry.service import ContainerRegistryService


class ContainerRegistryProcessors:
    get_container_registries: ActionProcessor[
        GetContainerRegistriesAction, GetContainerRegistriesActionResult
    ]

    def __init__(self, service: ContainerRegistryService) -> None:
        self.get_container_registries = ActionProcessor(service.get_container_registries)
