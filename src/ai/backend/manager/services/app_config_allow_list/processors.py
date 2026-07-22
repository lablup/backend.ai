from __future__ import annotations

from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor.global_action import GlobalActionProcessor
from ai.backend.manager.actions.processor.scope import ScopeActionProcessor
from ai.backend.manager.actions.processor.single_entity import SingleEntityActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.services.app_config_allow_list.actions.create import (
    CreateAppConfigAllowListAction,
    CreateAppConfigAllowListActionResult,
)
from ai.backend.manager.services.app_config_allow_list.actions.get import (
    GetAppConfigAllowListAction,
    GetAppConfigAllowListActionResult,
)
from ai.backend.manager.services.app_config_allow_list.actions.purge import (
    PurgeAppConfigAllowListAction,
    PurgeAppConfigAllowListActionResult,
)
from ai.backend.manager.services.app_config_allow_list.actions.search import (
    SearchAppConfigAllowListAction,
    SearchAppConfigAllowListActionResult,
)
from ai.backend.manager.services.app_config_allow_list.actions.update import (
    UpdateAppConfigAllowListAction,
    UpdateAppConfigAllowListActionResult,
)
from ai.backend.manager.services.app_config_allow_list.service import (
    AppConfigAllowListService,
)


class AppConfigAllowListProcessors(AbstractProcessorPackage):
    create: ScopeActionProcessor[
        CreateAppConfigAllowListAction, CreateAppConfigAllowListActionResult
    ]
    get: SingleEntityActionProcessor[GetAppConfigAllowListAction, GetAppConfigAllowListActionResult]
    search: GlobalActionProcessor[
        SearchAppConfigAllowListAction, SearchAppConfigAllowListActionResult
    ]
    update: SingleEntityActionProcessor[
        UpdateAppConfigAllowListAction, UpdateAppConfigAllowListActionResult
    ]
    purge: SingleEntityActionProcessor[
        PurgeAppConfigAllowListAction, PurgeAppConfigAllowListActionResult
    ]

    def __init__(
        self,
        service: AppConfigAllowListService,
        action_monitors: list[ActionMonitor],
    ) -> None:
        self.create = ScopeActionProcessor(service.create, action_monitors)
        self.get = SingleEntityActionProcessor(service.get, action_monitors)
        self.search = GlobalActionProcessor(service.search, action_monitors)
        self.update = SingleEntityActionProcessor(service.update, action_monitors)
        self.purge = SingleEntityActionProcessor(service.purge, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            CreateAppConfigAllowListAction.spec(),
            GetAppConfigAllowListAction.spec(),
            SearchAppConfigAllowListAction.spec(),
            UpdateAppConfigAllowListAction.spec(),
            PurgeAppConfigAllowListAction.spec(),
        ]
