from __future__ import annotations

from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor.scope import ScopeActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.services.app_config.actions.resolve import (
    ResolveAppConfigAction,
    ResolveAppConfigActionResult,
)
from ai.backend.manager.services.app_config.actions.resolve_bulk import (
    ResolveBulkAppConfigAction,
    ResolveBulkAppConfigActionResult,
)
from ai.backend.manager.services.app_config.actions.resolve_public import (
    ResolvePublicAppConfigAction,
    ResolvePublicAppConfigActionResult,
)
from ai.backend.manager.services.app_config.service import AppConfigService


class AppConfigProcessors(AbstractProcessorPackage):
    resolve: ScopeActionProcessor[ResolveAppConfigAction, ResolveAppConfigActionResult]
    resolve_bulk: ScopeActionProcessor[ResolveBulkAppConfigAction, ResolveBulkAppConfigActionResult]
    resolve_public: ScopeActionProcessor[
        ResolvePublicAppConfigAction, ResolvePublicAppConfigActionResult
    ]

    def __init__(
        self,
        service: AppConfigService,
        action_monitors: list[ActionMonitor],
    ) -> None:
        self.resolve = ScopeActionProcessor(service.resolve, action_monitors)
        self.resolve_bulk = ScopeActionProcessor(service.resolve_bulk, action_monitors)
        self.resolve_public = ScopeActionProcessor(service.resolve_public, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            ResolveAppConfigAction.spec(),
            ResolveBulkAppConfigAction.spec(),
            ResolvePublicAppConfigAction.spec(),
        ]
