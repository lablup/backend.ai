from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.services.artifact_registry.actions.huggingface.create import (
    CreateHuggingFaceRegistryAction,
    CreateHuggingFaceRegistryActionResult,
)
from ai.backend.manager.services.artifact_registry.actions.huggingface.delete import (
    DeleteHuggingFaceRegistryAction,
    DeleteHuggingFaceRegistryActionResult,
)
from ai.backend.manager.services.artifact_registry.actions.huggingface.get import (
    GetHuggingFaceRegistryAction,
    GetHuggingFaceRegistryActionResult,
)
from ai.backend.manager.services.artifact_registry.actions.huggingface.list import (
    ListHuggingFaceRegistryAction,
    ListHuggingFaceRegistryActionResult,
)
from ai.backend.manager.services.artifact_registry.actions.huggingface.update import (
    UpdateHuggingFaceRegistryAction,
    UpdateHuggingFaceRegistryActionResult,
)

from .service import ArtifactRegistryService


class ArtifactRegistryProcessors(AbstractProcessorPackage):
    create_huggingface_registry: ActionProcessor[
        CreateHuggingFaceRegistryAction, CreateHuggingFaceRegistryActionResult
    ]
    update_huggingface_registry: ActionProcessor[
        UpdateHuggingFaceRegistryAction, UpdateHuggingFaceRegistryActionResult
    ]
    delete_huggingface_registry: ActionProcessor[
        DeleteHuggingFaceRegistryAction, DeleteHuggingFaceRegistryActionResult
    ]
    get_huggingface_registry: ActionProcessor[
        GetHuggingFaceRegistryAction, GetHuggingFaceRegistryActionResult
    ]
    list_huggingface_registries: ActionProcessor[
        ListHuggingFaceRegistryAction, ListHuggingFaceRegistryActionResult
    ]

    def __init__(
        self, service: ArtifactRegistryService, action_monitors: list[ActionMonitor]
    ) -> None:
        self.create_huggingface_registry = ActionProcessor(
            service.create_huggingface_registry, action_monitors
        )
        self.update_huggingface_registry = ActionProcessor(
            service.update_huggingface_registry, action_monitors
        )
        self.delete_huggingface_registry = ActionProcessor(
            service.delete_huggingface_registry, action_monitors
        )
        self.get_huggingface_registry = ActionProcessor(
            service.get_huggingface_registry, action_monitors
        )
        self.list_huggingface_registries = ActionProcessor(
            service.list_huggingface_registry, action_monitors
        )

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            CreateHuggingFaceRegistryAction.spec(),
            UpdateHuggingFaceRegistryAction.spec(),
            DeleteHuggingFaceRegistryAction.spec(),
            GetHuggingFaceRegistryAction.spec(),
            ListHuggingFaceRegistryAction.spec(),
        ]
