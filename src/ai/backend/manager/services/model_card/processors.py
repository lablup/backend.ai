from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.services.model_card.actions.create import (
    CreateModelCardAction,
    CreateModelCardActionResult,
)
from ai.backend.manager.services.model_card.actions.delete import (
    DeleteModelCardAction,
    DeleteModelCardActionResult,
)
from ai.backend.manager.services.model_card.actions.search import (
    SearchModelCardsAction,
    SearchModelCardsActionResult,
)
from ai.backend.manager.services.model_card.actions.update import (
    UpdateModelCardAction,
    UpdateModelCardActionResult,
)
from ai.backend.manager.services.model_card.service import ModelCardService


class ModelCardProcessors(AbstractProcessorPackage):
    create: ActionProcessor[CreateModelCardAction, CreateModelCardActionResult]
    update: ActionProcessor[UpdateModelCardAction, UpdateModelCardActionResult]
    delete: ActionProcessor[DeleteModelCardAction, DeleteModelCardActionResult]
    search: ActionProcessor[SearchModelCardsAction, SearchModelCardsActionResult]

    def __init__(
        self,
        service: ModelCardService,
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
            CreateModelCardAction.spec(),
            UpdateModelCardAction.spec(),
            DeleteModelCardAction.spec(),
            SearchModelCardsAction.spec(),
        ]
