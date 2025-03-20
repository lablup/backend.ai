from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.services.resource.actions.list_presets import (
    ListResourcePresetsAction,
    ListResourcePresetsResult,
)
from ai.backend.manager.services.resource.service import ResourceService


class ResourceProcessors:
    list_presets: ActionProcessor[ListResourcePresetsAction, ListResourcePresetsResult]

    def __init__(self, service: ResourceService) -> None:
        self.list_presets = ActionProcessor(service.list_presets)
