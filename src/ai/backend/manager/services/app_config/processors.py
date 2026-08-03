from __future__ import annotations

from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor.scope import ScopeActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.services.app_config.actions.get import (
    GetAppConfigsAction,
    GetAppConfigsActionResult,
)
from ai.backend.manager.services.app_config.service import AppConfigService


class AppConfigProcessors(AbstractProcessorPackage):
    get_app_configs: ScopeActionProcessor[GetAppConfigsAction, GetAppConfigsActionResult]

    def __init__(
        self,
        service: AppConfigService,
        action_monitors: list[ActionMonitor],
    ) -> None:
        # No RBAC validator on purpose: the adapter fills the action's user_id from the
        # session, so a get is only ever for the acting user.
        self.get_app_configs = ScopeActionProcessor(service.get_app_configs, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            GetAppConfigsAction.spec(),
        ]
