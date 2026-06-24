from __future__ import annotations

from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor.scope import ScopeActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.services.app_config.actions.resolve import (
    ResolveAppConfigAction,
    ResolveAppConfigActionResult,
)
from ai.backend.manager.services.app_config.service import AppConfigService


class AppConfigProcessors(AbstractProcessorPackage):
    resolve: ScopeActionProcessor[ResolveAppConfigAction, ResolveAppConfigActionResult]

    def __init__(
        self,
        service: AppConfigService,
        action_monitors: list[ActionMonitor],
    ) -> None:
        self.resolve = ScopeActionProcessor(service.resolve, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            ResolveAppConfigAction.spec(),
        ]
