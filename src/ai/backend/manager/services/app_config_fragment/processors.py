from __future__ import annotations

from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor.scope import ScopeActionProcessor
from ai.backend.manager.actions.processor.single_entity import SingleEntityActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.services.app_config_fragment.actions.create import (
    CreateAppConfigFragmentAction,
    CreateAppConfigFragmentActionResult,
)
from ai.backend.manager.services.app_config_fragment.actions.get import (
    GetAppConfigFragmentAction,
    GetAppConfigFragmentActionResult,
)
from ai.backend.manager.services.app_config_fragment.actions.purge import (
    PurgeAppConfigFragmentAction,
    PurgeAppConfigFragmentActionResult,
)
from ai.backend.manager.services.app_config_fragment.actions.search import (
    SearchAppConfigFragmentAction,
    SearchAppConfigFragmentActionResult,
)
from ai.backend.manager.services.app_config_fragment.actions.update import (
    UpdateAppConfigFragmentAction,
    UpdateAppConfigFragmentActionResult,
)
from ai.backend.manager.services.app_config_fragment.service import (
    AppConfigFragmentService,
)


class AppConfigFragmentProcessors(AbstractProcessorPackage):
    create: ScopeActionProcessor[CreateAppConfigFragmentAction, CreateAppConfigFragmentActionResult]
    get: SingleEntityActionProcessor[GetAppConfigFragmentAction, GetAppConfigFragmentActionResult]
    search: ScopeActionProcessor[SearchAppConfigFragmentAction, SearchAppConfigFragmentActionResult]
    update: SingleEntityActionProcessor[
        UpdateAppConfigFragmentAction, UpdateAppConfigFragmentActionResult
    ]
    purge: SingleEntityActionProcessor[
        PurgeAppConfigFragmentAction, PurgeAppConfigFragmentActionResult
    ]

    def __init__(
        self,
        service: AppConfigFragmentService,
        action_monitors: list[ActionMonitor],
    ) -> None:
        self.create = ScopeActionProcessor(service.create, action_monitors)
        self.get = SingleEntityActionProcessor(service.get, action_monitors)
        self.search = ScopeActionProcessor(service.search, action_monitors)
        self.update = SingleEntityActionProcessor(service.update, action_monitors)
        self.purge = SingleEntityActionProcessor(service.purge, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            CreateAppConfigFragmentAction.spec(),
            GetAppConfigFragmentAction.spec(),
            SearchAppConfigFragmentAction.spec(),
            UpdateAppConfigFragmentAction.spec(),
            PurgeAppConfigFragmentAction.spec(),
        ]
