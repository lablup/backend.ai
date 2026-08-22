from typing import Any

from ai.backend.common.data.entity.model_card_resource_requirement import (
    MODEL_CARD_RESOURCE_REQUIREMENT_FIELD_TYPE,
)
from ai.backend.manager.actions.registry.field import LookupFieldGroup
from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.registry.types import FieldGroupMeta
from ai.backend.manager.actions.v2.bulk.processor import BulkActionProcessor
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.ops.result import (
    BatchOpsResult,
    CreatedEntityWithFieldsOpsResult,
    EntityOpsResult,
    ScopedBatchOpsResult,
    ScopedFieldsOpsResult,
)
from ai.backend.manager.actions.v2.scope.processor import ScopeActionProcessor
from ai.backend.manager.actions.v2.single_entity.processor import SingleEntityActionProcessor
from ai.backend.manager.data.model_card.types import (
    ModelCardData,
    ModelCardResourceRequirementData,
)
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
from ai.backend.manager.services.model_card.actions.lookup_requirement_owner import (
    LookupBulkModelCardResourceRequirementOwnerAction,
    LookupModelCardResourceRequirementOwnerAction,
)
from ai.backend.manager.services.model_card.actions.scan import (
    ScanProjectModelCardsAction,
    ScanProjectModelCardsActionResult,
)
from ai.backend.manager.services.model_card.actions.scoped_search_requirements import (
    ScopedSearchModelCardResourceRequirementsAction,
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
        CreatedEntityWithFieldsOpsResult[ModelCardData, ModelCardResourceRequirementData],
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
    scoped_search_requirements: BulkActionProcessor[
        ScopedSearchModelCardResourceRequirementsAction,
        ScopedFieldsOpsResult[ModelCardResourceRequirementData],
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

        requirements: LookupFieldGroup[ModelCardResourceRequirementData] = group.field_group(
            FieldGroupMeta(MODEL_CARD_RESOURCE_REQUIREMENT_FIELD_TYPE),
            ModelCardResourceRequirementData,
            LookupModelCardResourceRequirementOwnerAction,
            LookupBulkModelCardResourceRequirementOwnerAction,
        )
        self.scoped_search_requirements = requirements.bulk_scoped_search_ops(
            ScopedSearchModelCardResourceRequirementsAction
        )
