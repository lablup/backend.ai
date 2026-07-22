from __future__ import annotations

from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor.global_action import GlobalActionProcessor
from ai.backend.manager.actions.processor.scope import ScopeActionProcessor
from ai.backend.manager.actions.processor.single_entity import SingleEntityActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.services.app_config_definition.actions.create import (
    CreateAppConfigDefinitionAction,
    CreateAppConfigDefinitionActionResult,
)
from ai.backend.manager.services.app_config_definition.actions.get import (
    GetAppConfigDefinitionAction,
    GetAppConfigDefinitionActionResult,
)
from ai.backend.manager.services.app_config_definition.actions.purge import (
    PurgeAppConfigDefinitionAction,
    PurgeAppConfigDefinitionActionResult,
)
from ai.backend.manager.services.app_config_definition.actions.search import (
    SearchAppConfigDefinitionsAction,
    SearchAppConfigDefinitionsActionResult,
)
from ai.backend.manager.services.app_config_definition.service import (
    AppConfigDefinitionService,
)


class AppConfigDefinitionProcessors(AbstractProcessorPackage):
    create: ScopeActionProcessor[
        CreateAppConfigDefinitionAction, CreateAppConfigDefinitionActionResult
    ]
    get: SingleEntityActionProcessor[
        GetAppConfigDefinitionAction, GetAppConfigDefinitionActionResult
    ]
    search: GlobalActionProcessor[
        SearchAppConfigDefinitionsAction, SearchAppConfigDefinitionsActionResult
    ]
    purge: SingleEntityActionProcessor[
        PurgeAppConfigDefinitionAction, PurgeAppConfigDefinitionActionResult
    ]

    def __init__(
        self,
        service: AppConfigDefinitionService,
        action_monitors: list[ActionMonitor],
    ) -> None:
        self.create = ScopeActionProcessor(service.create, action_monitors)
        self.get = SingleEntityActionProcessor(service.get, action_monitors)
        self.search = GlobalActionProcessor(service.search, action_monitors)
        self.purge = SingleEntityActionProcessor(service.purge, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            CreateAppConfigDefinitionAction.spec(),
            GetAppConfigDefinitionAction.spec(),
            SearchAppConfigDefinitionsAction.spec(),
            PurgeAppConfigDefinitionAction.spec(),
        ]
