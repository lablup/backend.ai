from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.processor.scope import ScopeActionProcessor
from ai.backend.manager.actions.processor.single_entity import SingleEntityActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.services.artifact_registry.actions.common.get_meta import (
    GetArtifactRegistryMetaAction,
    GetArtifactRegistryMetaActionResult,
)
from ai.backend.manager.services.artifact_registry.actions.common.get_multi import (
    GetArtifactRegistryMetasAction,
    GetArtifactRegistryMetasActionResult,
)
from ai.backend.manager.services.artifact_registry.actions.common.search import (
    SearchArtifactRegistriesAction,
    SearchArtifactRegistriesActionResult,
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
from ai.backend.manager.services.artifact_registry.actions.huggingface.search import (
    SearchHuggingFaceRegistriesAction,
    SearchHuggingFaceRegistriesActionResult,
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
from ai.backend.manager.services.artifact_registry.actions.reservoir.search import (
    SearchReservoirRegistriesAction,
    SearchReservoirRegistriesActionResult,
)
from ai.backend.manager.services.artifact_registry.actions.reservoir.update import (
    UpdateReservoirRegistryAction,
    UpdateReservoirRegistryActionResult,
)

from .service import ArtifactRegistryService


class ArtifactRegistryProcessors(AbstractProcessorPackage):
    create_huggingface_registry: ScopeActionProcessor[
        CreateHuggingFaceRegistryAction, CreateHuggingFaceRegistryActionResult
    ]
    update_huggingface_registry: SingleEntityActionProcessor[
        UpdateHuggingFaceRegistryAction, UpdateHuggingFaceRegistryActionResult
    ]
    delete_huggingface_registry: SingleEntityActionProcessor[
        DeleteHuggingFaceRegistryAction, DeleteHuggingFaceRegistryActionResult
    ]
    get_huggingface_registry: SingleEntityActionProcessor[
        GetHuggingFaceRegistryAction, GetHuggingFaceRegistryActionResult
    ]
    get_huggingface_registries: ActionProcessor[
        GetHuggingFaceRegistriesAction, GetHuggingFaceRegistriesActionResult
    ]
    list_huggingface_registries: ScopeActionProcessor[
        ListHuggingFaceRegistryAction, ListHuggingFaceRegistryActionResult
    ]
    search_huggingface_registries: ScopeActionProcessor[
        SearchHuggingFaceRegistriesAction, SearchHuggingFaceRegistriesActionResult
    ]
    create_reservoir_registry: ScopeActionProcessor[
        CreateReservoirRegistryAction, CreateReservoirActionResult
    ]
    update_reservoir_registry: SingleEntityActionProcessor[
        UpdateReservoirRegistryAction, UpdateReservoirRegistryActionResult
    ]
    delete_reservoir_registry: SingleEntityActionProcessor[
        DeleteReservoirRegistryAction, DeleteReservoirActionResult
    ]
    get_reservoir_registry: SingleEntityActionProcessor[
        GetReservoirRegistryAction, GetReservoirRegistryActionResult
    ]
    get_reservoir_registries: ActionProcessor[
        GetReservoirRegistriesAction, GetReservoirRegistriesActionResult
    ]
    list_reservoir_registries: ScopeActionProcessor[
        ListReservoirRegistriesAction, ListReservoirRegistriesActionResult
    ]
    search_reservoir_registries: ScopeActionProcessor[
        SearchReservoirRegistriesAction, SearchReservoirRegistriesActionResult
    ]
    get_registry_meta: ActionProcessor[
        GetArtifactRegistryMetaAction, GetArtifactRegistryMetaActionResult
    ]
    get_registry_metas: ActionProcessor[
        GetArtifactRegistryMetasAction, GetArtifactRegistryMetasActionResult
    ]
    search_artifact_registries: ScopeActionProcessor[
        SearchArtifactRegistriesAction, SearchArtifactRegistriesActionResult
    ]

    def __init__(
        self,
        service: ArtifactRegistryService,
        action_monitors: list[ActionMonitor],
        validators: ActionValidators,
    ) -> None:
        # Scope actions with RBAC validator
        self.create_huggingface_registry = ScopeActionProcessor(
            service.create_huggingface_registry, action_monitors, validators=[validators.rbac.scope]
        )
        self.list_huggingface_registries = ScopeActionProcessor(
            service.list_huggingface_registry, action_monitors, validators=[validators.rbac.scope]
        )
        self.search_huggingface_registries = ScopeActionProcessor(
            service.search_huggingface_registries,
            action_monitors,
            validators=[validators.rbac.scope],
        )
        self.create_reservoir_registry = ScopeActionProcessor(
            service.create_reservoir_registry, action_monitors, validators=[validators.rbac.scope]
        )
        self.list_reservoir_registries = ScopeActionProcessor(
            service.list_reservoir_registries, action_monitors, validators=[validators.rbac.scope]
        )
        self.search_reservoir_registries = ScopeActionProcessor(
            service.search_reservoir_registries, action_monitors, validators=[validators.rbac.scope]
        )
        self.search_artifact_registries = ScopeActionProcessor(
            service.search_artifact_registries, action_monitors, validators=[validators.rbac.scope]
        )

        # Single entity actions with RBAC validator
        self.update_huggingface_registry = SingleEntityActionProcessor(
            service.update_huggingface_registry,
            action_monitors,
            validators=[validators.rbac.single_entity],
        )
        self.delete_huggingface_registry = SingleEntityActionProcessor(
            service.delete_huggingface_registry,
            action_monitors,
            validators=[validators.rbac.single_entity],
        )
        self.get_huggingface_registry = SingleEntityActionProcessor(
            service.get_huggingface_registry,
            action_monitors,
            validators=[validators.rbac.single_entity],
        )
        self.update_reservoir_registry = SingleEntityActionProcessor(
            service.update_reservoir_registry,
            action_monitors,
            validators=[validators.rbac.single_entity],
        )
        self.delete_reservoir_registry = SingleEntityActionProcessor(
            service.delete_reservoir_registry,
            action_monitors,
            validators=[validators.rbac.single_entity],
        )
        self.get_reservoir_registry = SingleEntityActionProcessor(
            service.get_reservoir_registry,
            action_monitors,
            validators=[validators.rbac.single_entity],
        )

        # Internal/batch actions without RBAC
        self.get_huggingface_registries = ActionProcessor(
            service.get_huggingface_registries, action_monitors
        )
        self.get_reservoir_registries = ActionProcessor(
            service.get_reservoir_registries, action_monitors
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
            SearchHuggingFaceRegistriesAction.spec(),
            CreateReservoirRegistryAction.spec(),
            UpdateReservoirRegistryAction.spec(),
            DeleteReservoirRegistryAction.spec(),
            GetReservoirRegistryAction.spec(),
            GetReservoirRegistriesAction.spec(),
            ListReservoirRegistriesAction.spec(),
            SearchReservoirRegistriesAction.spec(),
            GetArtifactRegistryMetaAction.spec(),
            GetArtifactRegistryMetasAction.spec(),
            SearchArtifactRegistriesAction.spec(),
        ]
