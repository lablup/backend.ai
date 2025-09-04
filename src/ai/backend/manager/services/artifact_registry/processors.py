from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.services.artifact_registry.actions.common.get_meta import (
    GetArtifactRegistryMetaAction,
    GetArtifactRegistryMetaActionResult,
)
from ai.backend.manager.services.artifact_registry.actions.common.get_multi import (
    GetArtifactRegistryMetasAction,
    GetArtifactRegistryMetasActionResult,
)
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
from ai.backend.manager.services.artifact_registry.actions.huggingface.get_multi import (
    GetHuggingFaceRegistriesAction,
    GetHuggingFaceRegistriesActionResult,
)
from ai.backend.manager.services.artifact_registry.actions.huggingface.list import (
    ListHuggingFaceRegistryAction,
    ListHuggingFaceRegistryActionResult,
)
from ai.backend.manager.services.artifact_registry.actions.huggingface.update import (
    UpdateHuggingFaceRegistryAction,
    UpdateHuggingFaceRegistryActionResult,
)
from ai.backend.manager.services.artifact_registry.actions.reservoir.create import (
    CreateReservoirActionResult,
    CreateReservoirRegistryAction,
)
from ai.backend.manager.services.artifact_registry.actions.reservoir.delete import (
    DeleteReservoirActionResult,
    DeleteReservoirRegistryAction,
)
from ai.backend.manager.services.artifact_registry.actions.reservoir.get import (
    GetReservoirRegistryAction,
    GetReservoirRegistryActionResult,
)
from ai.backend.manager.services.artifact_registry.actions.reservoir.get_multi import (
    GetReservoirRegistriesAction,
    GetReservoirRegistriesActionResult,
)
from ai.backend.manager.services.artifact_registry.actions.reservoir.list import (
    ListReservoirRegistriesAction,
    ListReservoirRegistriesActionResult,
)
from ai.backend.manager.services.artifact_registry.actions.reservoir.update import (
    UpdateReservoirRegistryAction,
    UpdateReservoirRegistryActionResult,
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
    get_huggingface_registries: ActionProcessor[
        GetHuggingFaceRegistriesAction, GetHuggingFaceRegistriesActionResult
    ]
    list_huggingface_registries: ActionProcessor[
        ListHuggingFaceRegistryAction, ListHuggingFaceRegistryActionResult
    ]
    create_reservoir_registry: ActionProcessor[
        CreateReservoirRegistryAction, CreateReservoirActionResult
    ]
    update_reservoir_registry: ActionProcessor[
        UpdateReservoirRegistryAction, UpdateReservoirRegistryActionResult
    ]
    delete_reservoir_registry: ActionProcessor[
        DeleteReservoirRegistryAction, DeleteReservoirActionResult
    ]
    get_reservoir_registry: ActionProcessor[
        GetReservoirRegistryAction, GetReservoirRegistryActionResult
    ]
    get_reservoir_registries: ActionProcessor[
        GetReservoirRegistriesAction, GetReservoirRegistriesActionResult
    ]
    list_reservoir_registries: ActionProcessor[
        ListReservoirRegistriesAction, ListReservoirRegistriesActionResult
    ]
    get_registry_meta: ActionProcessor[
        GetArtifactRegistryMetaAction, GetArtifactRegistryMetaActionResult
    ]
    get_registry_metas: ActionProcessor[
        GetArtifactRegistryMetasAction, GetArtifactRegistryMetasActionResult
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
        self.get_huggingface_registries = ActionProcessor(
            service.get_huggingface_registries, action_monitors
        )
        self.list_huggingface_registries = ActionProcessor(
            service.list_huggingface_registry, action_monitors
        )
        self.create_reservoir_registry = ActionProcessor(
            service.create_reservoir_registry, action_monitors
        )
        self.update_reservoir_registry = ActionProcessor(
            service.update_reservoir_registry, action_monitors
        )
        self.delete_reservoir_registry = ActionProcessor(
            service.delete_reservoir_registry, action_monitors
        )
        self.get_reservoir_registry = ActionProcessor(
            service.get_reservoir_registry, action_monitors
        )
        self.get_reservoir_registries = ActionProcessor(
            service.get_reservoir_registries, action_monitors
        )
        self.list_reservoir_registries = ActionProcessor(
            service.list_reservoir_registries, action_monitors
        )
        self.get_registry_meta = ActionProcessor(service.get_registry_meta, action_monitors)
        self.get_registry_metas = ActionProcessor(service.get_registry_metas, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            CreateHuggingFaceRegistryAction.spec(),
            UpdateHuggingFaceRegistryAction.spec(),
            DeleteHuggingFaceRegistryAction.spec(),
            GetHuggingFaceRegistryAction.spec(),
            GetHuggingFaceRegistriesAction.spec(),
            ListHuggingFaceRegistryAction.spec(),
            CreateReservoirRegistryAction.spec(),
            UpdateReservoirRegistryAction.spec(),
            DeleteReservoirRegistryAction.spec(),
            GetReservoirRegistryAction.spec(),
            GetReservoirRegistriesAction.spec(),
            ListReservoirRegistriesAction.spec(),
            GetArtifactRegistryMetaAction.spec(),
            GetArtifactRegistryMetasAction.spec(),
        ]
