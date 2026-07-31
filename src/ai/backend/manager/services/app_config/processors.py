from __future__ import annotations

from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor.scope import ScopeActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.services.app_config.actions.resolve import (
    ResolveAppConfigsAction,
    ResolveAppConfigsActionResult,
)
from ai.backend.manager.services.app_config.service import AppConfigService


class AppConfigProcessors(AbstractProcessorPackage):
    resolve_app_configs: ScopeActionProcessor[
        ResolveAppConfigsAction, ResolveAppConfigsActionResult
    ]

    def __init__(
        self,
        service: AppConfigService,
        action_monitors: list[ActionMonitor],
    ) -> None:
        # No RBAC validator on purpose: the handler fills the action's user_id from the
        # session, so a resolve is only ever for the acting user.
        self.resolve_app_configs = ScopeActionProcessor(
            service.resolve_app_configs, action_monitors
        )

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            ResolveAppConfigsAction.spec(),
        ]
