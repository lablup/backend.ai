from typing import Any

from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.ops.result import (
    BatchOpsResult,
    CreatedEntityWithFieldsOpsResult,
    EntityOpsResult,
    ScopedBatchOpsResult,
)
from ai.backend.manager.actions.v2.scope.processor import ScopeActionProcessor
from ai.backend.manager.actions.v2.single_entity.processor import SingleEntityActionProcessor
from ai.backend.manager.data.model_card.types import ModelCardData, ResourceRequirementEntry
from ai.backend.manager.services.model_card.actions.available_presets import (
    AvailablePresetsAction,
    AvailablePresetsActionResult,
)
from ai.backend.manager.services.model_card.actions.bulk_delete import (
    BulkDeleteModelCardAction,
    BulkDeleteModelCardActionResult,
)
from ai.backend.manager.services.model_card.actions.create import CreateModelCardAction
from ai.backend.manager.services.model_card.actions.delete import (
    DeleteModelCardAction,
    DeleteModelCardActionResult,
)
from ai.backend.manager.services.model_card.actions.get import GetModelCardAction
from ai.backend.manager.services.model_card.actions.min_resources import (
    GetModelCardMinResourcesAction,
    GetModelCardMinResourcesActionResult,
)
from ai.backend.manager.services.model_card.actions.scan import (
    ScanProjectModelCardsAction,
    ScanProjectModelCardsActionResult,
)
from ai.backend.manager.services.model_card.actions.search import (
    GlobalSearchModelCardsAction,
)
from ai.backend.manager.services.model_card.actions.search_in_project import (
    SearchModelCardsInProjectAction,
)
from ai.backend.manager.services.model_card.actions.update import (
    UpdateModelCardAction,
    UpdateModelCardActionResult,
)
from ai.backend.manager.services.model_card.service import ModelCardService


class ModelCardProcessors:
    create: ScopeActionProcessor[
        CreateModelCardAction,
        CreatedEntityWithFieldsOpsResult[ModelCardData, ResourceRequirementEntry],
    ]
    update: SingleEntityActionProcessor[UpdateModelCardAction, UpdateModelCardActionResult]
    delete: SingleEntityActionProcessor[DeleteModelCardAction, DeleteModelCardActionResult]
    bulk_delete: GlobalActionProcessor[BulkDeleteModelCardAction, BulkDeleteModelCardActionResult]
    get: SingleEntityActionProcessor[GetModelCardAction, EntityOpsResult[ModelCardData]]
    global_search: GlobalActionProcessor[
        GlobalSearchModelCardsAction, BatchOpsResult[ModelCardData]
    ]
    search_in_project: ScopeActionProcessor[
        SearchModelCardsInProjectAction, ScopedBatchOpsResult[ModelCardData]
    ]
    scan: GlobalActionProcessor[ScanProjectModelCardsAction, ScanProjectModelCardsActionResult]
    available_presets: GlobalActionProcessor[AvailablePresetsAction, AvailablePresetsActionResult]
    get_min_resources: GlobalActionProcessor[
        GetModelCardMinResourcesAction, GetModelCardMinResourcesActionResult
    ]

    def __init__(self, group: ProcessorGroup[Any], service: ModelCardService) -> None:
        self.create = group.entity_create_with_fields_ops(CreateModelCardAction)
        self.update = group.single_entity(UpdateModelCardAction, service.update)
        self.delete = group.single_entity(DeleteModelCardAction, service.delete)
        self.bulk_delete = group.global_scope(BulkDeleteModelCardAction, service.bulk_delete)
        self.get = group.single_get_ops(GetModelCardAction)
        self.global_search = group.global_search_ops(GlobalSearchModelCardsAction)
        self.search_in_project = group.scope_search_ops(SearchModelCardsInProjectAction)
        self.scan = group.global_scope(ScanProjectModelCardsAction, service.scan)
        self.available_presets = group.global_scope(
            AvailablePresetsAction, service.available_presets
        )
        self.get_min_resources = group.global_scope(
            GetModelCardMinResourcesAction, service.get_min_resources
        )
