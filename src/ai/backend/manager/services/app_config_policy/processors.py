from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor.bulk import BulkActionProcessor
from ai.backend.manager.actions.processor.single_entity import SingleEntityActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.services.app_config_policy.actions.get import (
    GetAppConfigPolicyAction,
    GetAppConfigPolicyActionResult,
)
from ai.backend.manager.services.app_config_policy.actions.scoped_search import (
    ScopedSearchAppConfigPoliciesAction,
    ScopedSearchAppConfigPoliciesActionResult,
)
from ai.backend.manager.services.app_config_policy.service import AppConfigPolicyService


class AppConfigPolicyProcessors(AbstractProcessorPackage):
    get: SingleEntityActionProcessor[GetAppConfigPolicyAction, GetAppConfigPolicyActionResult]
    scoped_search: BulkActionProcessor[
        ScopedSearchAppConfigPoliciesAction, ScopedSearchAppConfigPoliciesActionResult
    ]

    def __init__(
        self,
        service: AppConfigPolicyService,
        action_monitors: list[ActionMonitor],
        validators: ActionValidators,
    ) -> None:
        self.get = SingleEntityActionProcessor(service.get, action_monitors)
        self.scoped_search = BulkActionProcessor(service.scoped_search, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            GetAppConfigPolicyAction.spec(),
            ScopedSearchAppConfigPoliciesAction.spec(),
        ]
