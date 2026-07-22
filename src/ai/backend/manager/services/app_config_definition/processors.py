from __future__ import annotations

from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor.global_action import GlobalActionProcessor
from ai.backend.manager.actions.processor.scope import ScopeActionProcessor
from ai.backend.manager.actions.processor.single_entity import SingleEntityActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.services.app_config_definition.actions.admin_search import (
    AdminAdminSearchAppConfigDefinitionsActionResult,
    AdminSearchAppConfigDefinitionsAction,
)
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
    admin_search: GlobalActionProcessor[
        AdminSearchAppConfigDefinitionsAction, AdminAdminSearchAppConfigDefinitionsActionResult
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
        self.admin_search = GlobalActionProcessor(service.admin_search, action_monitors)
        self.purge = SingleEntityActionProcessor(service.purge, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            CreateAppConfigDefinitionAction.spec(),
            GetAppConfigDefinitionAction.spec(),
            AdminSearchAppConfigDefinitionsAction.spec(),
            PurgeAppConfigDefinitionAction.spec(),
        ]
