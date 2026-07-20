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
from ai.backend.manager.services.app_config.service import AppConfigService


class AppConfigProcessors(AbstractProcessorPackage):
    resolve_app_config: ScopeActionProcessor[ResolveAppConfigAction, ResolveAppConfigActionResult]
    resolve_app_config_bulk: ScopeActionProcessor[
        ResolveBulkAppConfigAction, ResolveBulkAppConfigActionResult
    ]

    def __init__(
        self,
        service: AppConfigService,
        action_monitors: list[ActionMonitor],
    ) -> None:
        # No RBAC validator is injected here on purpose. The allow-list registers which
        # (config_name, scope_type) pairs merge and at what rank — it carries no user
        # dimension, so it cannot keep one user from naming another's principal. That is
        # the service's own check (``_authorize_resolve_principal``): the resolving
        # user_id must be the acting user's own, superadmins excepted.
        self.resolve_app_config = ScopeActionProcessor(service.resolve_app_config, action_monitors)
        self.resolve_app_config_bulk = ScopeActionProcessor(
            service.resolve_app_config_bulk, action_monitors
        )

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            ResolveAppConfigAction.spec(),
            ResolveBulkAppConfigAction.spec(),
        ]
