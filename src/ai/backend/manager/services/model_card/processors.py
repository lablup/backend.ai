from typing import Any

from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.services.model_card.actions.available_presets import (
    AvailablePresetsAction,
    AvailablePresetsActionResult,
)
from ai.backend.manager.services.model_card.actions.bulk_delete import (
    BulkDeleteModelCardAction,
    BulkDeleteModelCardActionResult,
)
from ai.backend.manager.services.model_card.actions.create import (
    CreateModelCardAction,
    CreateModelCardActionResult,
)
from ai.backend.manager.services.model_card.actions.delete import (
    DeleteModelCardAction,
    DeleteModelCardActionResult,
)
from ai.backend.manager.services.model_card.actions.min_resources import (
    GetModelCardMinResourcesAction,
    GetModelCardMinResourcesActionResult,
)
from ai.backend.manager.services.model_card.actions.scan import (
    ScanProjectModelCardsAction,
    ScanProjectModelCardsActionResult,
)
from ai.backend.manager.services.model_card.actions.search import (
    SearchModelCardsAction,
    SearchModelCardsActionResult,
)
from ai.backend.manager.services.model_card.actions.search_in_project import (
    SearchModelCardsInProjectAction,
    SearchModelCardsInProjectActionResult,
)
from ai.backend.manager.services.model_card.actions.update import (
    UpdateModelCardAction,
    UpdateModelCardActionResult,
)
from ai.backend.manager.services.model_card.service import ModelCardService


class ModelCardProcessors:
    create: GlobalActionProcessor[CreateModelCardAction, CreateModelCardActionResult]
    update: GlobalActionProcessor[UpdateModelCardAction, UpdateModelCardActionResult]
    delete: GlobalActionProcessor[DeleteModelCardAction, DeleteModelCardActionResult]
    bulk_delete: GlobalActionProcessor[BulkDeleteModelCardAction, BulkDeleteModelCardActionResult]
    search: GlobalActionProcessor[SearchModelCardsAction, SearchModelCardsActionResult]
    search_in_project: GlobalActionProcessor[
        SearchModelCardsInProjectAction, SearchModelCardsInProjectActionResult
    ]
    scan: GlobalActionProcessor[ScanProjectModelCardsAction, ScanProjectModelCardsActionResult]
    available_presets: GlobalActionProcessor[AvailablePresetsAction, AvailablePresetsActionResult]
    get_min_resources: GlobalActionProcessor[
        GetModelCardMinResourcesAction, GetModelCardMinResourcesActionResult
    ]

    def __init__(self, group: ProcessorGroup[Any], service: ModelCardService) -> None:
        self.create = group.global_scope(CreateModelCardAction, service.create)
        self.update = group.global_scope(UpdateModelCardAction, service.update)
        self.delete = group.global_scope(DeleteModelCardAction, service.delete)
        self.bulk_delete = group.global_scope(BulkDeleteModelCardAction, service.bulk_delete)
        self.search = group.global_scope(SearchModelCardsAction, service.search)
        self.search_in_project = group.global_scope(
            SearchModelCardsInProjectAction, service.search_in_project
        )
        self.scan = group.global_scope(ScanProjectModelCardsAction, service.scan)
        self.available_presets = group.global_scope(
            AvailablePresetsAction, service.available_presets
        )
        self.get_min_resources = group.global_scope(
            GetModelCardMinResourcesAction, service.get_min_resources
        )
