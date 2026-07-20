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
    resolve_app_config: ScopeActionProcessor[ResolveAppConfigAction, ResolveAppConfigActionResult]

    def __init__(
        self,
        service: AppConfigService,
        action_monitors: list[ActionMonitor],
    ) -> None:
        # No RBAC validator is injected here on purpose, and none is needed to keep a
        # caller out of another user's config: the action carries no user_id at all. The
        # service injects it from the session, so a resolve can only ever be for the
        # acting user. (The allow-list could not have done this — it registers which
        # (config_name, scope_type) pairs merge and at what rank, with no user dimension.)
        self.resolve_app_config = ScopeActionProcessor(service.resolve_app_config, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            ResolveAppConfigAction.spec(),
        ]
