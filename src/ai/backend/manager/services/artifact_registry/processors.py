from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.lookup.processor import LookupActionProcessor
from ai.backend.manager.actions.v2.ops.result import LookupOpsResult
from ai.backend.manager.actions.v2.single_entity.processor import SingleEntityActionProcessor
from ai.backend.manager.data.artifact_registries.types import ArtifactRegistryData
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
from ai.backend.manager.services.artifact_registry.actions.lookup import (
    LookupArtifactRegistryAction,
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


class ArtifactRegistryProcessors:
    lookup: LookupActionProcessor[
        LookupArtifactRegistryAction, LookupOpsResult[ArtifactRegistryData]
    ]
    create_huggingface_registry: GlobalActionProcessor[
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
    get_huggingface_registries: GlobalActionProcessor[
        GetHuggingFaceRegistriesAction, GetHuggingFaceRegistriesActionResult
    ]
    list_huggingface_registries: GlobalActionProcessor[
        ListHuggingFaceRegistryAction, ListHuggingFaceRegistryActionResult
    ]
    search_huggingface_registries: GlobalActionProcessor[
        SearchHuggingFaceRegistriesAction, SearchHuggingFaceRegistriesActionResult
    ]
    create_reservoir_registry: GlobalActionProcessor[
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
    get_reservoir_registries: GlobalActionProcessor[
        GetReservoirRegistriesAction, GetReservoirRegistriesActionResult
    ]
    list_reservoir_registries: GlobalActionProcessor[
        ListReservoirRegistriesAction, ListReservoirRegistriesActionResult
    ]
    search_reservoir_registries: GlobalActionProcessor[
        SearchReservoirRegistriesAction, SearchReservoirRegistriesActionResult
    ]
    get_registry_meta: SingleEntityActionProcessor[
        GetArtifactRegistryMetaAction, GetArtifactRegistryMetaActionResult
    ]
    get_registry_metas: GlobalActionProcessor[
        GetArtifactRegistryMetasAction, GetArtifactRegistryMetasActionResult
    ]
    search_artifact_registries: GlobalActionProcessor[
        SearchArtifactRegistriesAction, SearchArtifactRegistriesActionResult
    ]

    def __init__(
        self, group: ProcessorGroup[ArtifactRegistryData], service: ArtifactRegistryService
    ) -> None:
        self.lookup = group.public_lookup_ops(LookupArtifactRegistryAction)
        # Scope actions with RBAC validator
        self.create_huggingface_registry = group.global_scope(
            CreateHuggingFaceRegistryAction, service.create_huggingface_registry
        )
        self.list_huggingface_registries = group.global_scope(
            ListHuggingFaceRegistryAction, service.list_huggingface_registry
        )
        self.search_huggingface_registries = group.global_scope(
            SearchHuggingFaceRegistriesAction, service.search_huggingface_registries
        )
        self.create_reservoir_registry = group.global_scope(
            CreateReservoirRegistryAction, service.create_reservoir_registry
        )
        self.list_reservoir_registries = group.global_scope(
            ListReservoirRegistriesAction, service.list_reservoir_registries
        )
        self.search_reservoir_registries = group.global_scope(
            SearchReservoirRegistriesAction, service.search_reservoir_registries
        )
        self.search_artifact_registries = group.global_scope(
            SearchArtifactRegistriesAction, service.search_artifact_registries
        )

        # Single entity actions with RBAC validator
        self.update_huggingface_registry = group.single_entity(
            UpdateHuggingFaceRegistryAction, service.update_huggingface_registry
        )
        self.delete_huggingface_registry = group.single_entity(
            DeleteHuggingFaceRegistryAction, service.delete_huggingface_registry
        )
        self.get_huggingface_registry = group.single_entity(
            GetHuggingFaceRegistryAction, service.get_huggingface_registry
        )
        self.update_reservoir_registry = group.single_entity(
            UpdateReservoirRegistryAction, service.update_reservoir_registry
        )
        self.delete_reservoir_registry = group.single_entity(
            DeleteReservoirRegistryAction, service.delete_reservoir_registry
        )
        self.get_reservoir_registry = group.single_entity(
            GetReservoirRegistryAction, service.get_reservoir_registry
        )

        self.get_registry_meta = group.single_entity(
            GetArtifactRegistryMetaAction, service.get_registry_meta
        )

        # Internal/batch actions without RBAC
        self.get_huggingface_registries = group.global_scope(
            GetHuggingFaceRegistriesAction, service.get_huggingface_registries
        )
        self.get_reservoir_registries = group.global_scope(
            GetReservoirRegistriesAction, service.get_reservoir_registries
        )
        self.get_registry_metas = group.global_scope(
            GetArtifactRegistryMetasAction, service.get_registry_metas
        )
