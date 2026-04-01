from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.services.runtime_variant.actions.create import (
    CreateRuntimeVariantAction,
    CreateRuntimeVariantActionResult,
)
from ai.backend.manager.services.runtime_variant.actions.delete import (
    DeleteRuntimeVariantAction,
    DeleteRuntimeVariantActionResult,
)
from ai.backend.manager.services.runtime_variant.actions.search import (
    SearchRuntimeVariantsAction,
    SearchRuntimeVariantsActionResult,
)
from ai.backend.manager.services.runtime_variant.actions.update import (
    UpdateRuntimeVariantAction,
    UpdateRuntimeVariantActionResult,
)
from ai.backend.manager.services.runtime_variant.service import RuntimeVariantService


class RuntimeVariantProcessors(AbstractProcessorPackage):
    create: ActionProcessor[CreateRuntimeVariantAction, CreateRuntimeVariantActionResult]
    update: ActionProcessor[UpdateRuntimeVariantAction, UpdateRuntimeVariantActionResult]
    delete: ActionProcessor[DeleteRuntimeVariantAction, DeleteRuntimeVariantActionResult]
    search: ActionProcessor[SearchRuntimeVariantsAction, SearchRuntimeVariantsActionResult]

    def __init__(
        self,
        service: RuntimeVariantService,
        action_monitors: list[ActionMonitor],
        validators: ActionValidators,
    ) -> None:
        self.create = ActionProcessor(service.create, action_monitors)
        self.update = ActionProcessor(service.update, action_monitors)
        self.delete = ActionProcessor(service.delete, action_monitors)
        self.search = ActionProcessor(service.search, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            CreateRuntimeVariantAction.spec(),
            UpdateRuntimeVariantAction.spec(),
            DeleteRuntimeVariantAction.spec(),
            SearchRuntimeVariantsAction.spec(),
        ]
