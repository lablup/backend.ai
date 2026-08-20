from __future__ import annotations

from ai.backend.manager.actions.registry.field import LookupFieldGroup
from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.ops.result import (
    BatchOpsResult,
    CreatedEntityWithFieldsOpsResult,
    EntityOpsResult,
    ScopedFieldsOpsResult,
)
from ai.backend.manager.actions.v2.scope.processor import ScopeActionProcessor
from ai.backend.manager.actions.v2.single_entity.processor import SingleEntityActionProcessor
from ai.backend.manager.data.deployment_preset.types import PresetResourceSlotData
from ai.backend.manager.data.deployment_revision_preset.types import (
    DeploymentRevisionPresetData,
    ResourceSlotEntryData,
)
from ai.backend.manager.services.deployment_revision_preset.actions.create import (
    CreateDeploymentPresetAction,
)
from ai.backend.manager.services.deployment_revision_preset.actions.get import (
    GetDeploymentPresetAction,
)
from ai.backend.manager.services.deployment_revision_preset.actions.purge import (
    PurgeDeploymentPresetAction,
)
from ai.backend.manager.services.deployment_revision_preset.actions.search import (
    GlobalSearchDeploymentPresetsAction,
)
from ai.backend.manager.services.deployment_revision_preset.actions.search_resource_slots import (
    SearchPresetResourceSlotsAction,
)
from ai.backend.manager.services.deployment_revision_preset.actions.update import (
    UpdateDeploymentPresetAction,
)
from ai.backend.manager.services.deployment_revision_preset.service import DeploymentPresetService


class DeploymentPresetProcessors:
    """An update restates the preset's slots, so it goes through the service; the rest
    run straight against ops."""

    create: GlobalActionProcessor[
        CreateDeploymentPresetAction,
        CreatedEntityWithFieldsOpsResult[DeploymentRevisionPresetData, ResourceSlotEntryData],
    ]
    get: SingleEntityActionProcessor[
        GetDeploymentPresetAction, EntityOpsResult[DeploymentRevisionPresetData]
    ]
    global_search: GlobalActionProcessor[
        GlobalSearchDeploymentPresetsAction, BatchOpsResult[DeploymentRevisionPresetData]
    ]
    update: SingleEntityActionProcessor[
        UpdateDeploymentPresetAction, EntityOpsResult[DeploymentRevisionPresetData]
    ]
    purge: SingleEntityActionProcessor[
        PurgeDeploymentPresetAction, EntityOpsResult[DeploymentRevisionPresetData]
    ]
    search_resource_slots: ScopeActionProcessor[
        SearchPresetResourceSlotsAction, ScopedFieldsOpsResult[PresetResourceSlotData]
    ]

    def __init__(
        self,
        group: ProcessorGroup[DeploymentRevisionPresetData],
        slots: LookupFieldGroup[PresetResourceSlotData],
        service: DeploymentPresetService,
    ) -> None:
        self.create = group.global_create_with_fields_ops(CreateDeploymentPresetAction)
        self.get = group.single_get_ops(GetDeploymentPresetAction)
        self.global_search = group.global_search_ops(GlobalSearchDeploymentPresetsAction)
        self.update = group.single_entity(UpdateDeploymentPresetAction, service.update)
        self.purge = group.entity_purge_ops(PurgeDeploymentPresetAction)
        self.search_resource_slots = slots.search_ops(SearchPresetResourceSlotsAction)
