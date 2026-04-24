from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.services.app_config_policy.actions.create import (
    CreateAppConfigPolicyAction,
    CreateAppConfigPolicyActionResult,
)
from ai.backend.manager.services.app_config_policy.actions.get import (
    GetAppConfigPolicyAction,
    GetAppConfigPolicyActionResult,
)
from ai.backend.manager.services.app_config_policy.actions.purge import (
    PurgeAppConfigPolicyAction,
    PurgeAppConfigPolicyActionResult,
)
from ai.backend.manager.services.app_config_policy.actions.search import (
    SearchAppConfigPoliciesAction,
    SearchAppConfigPoliciesActionResult,
)
from ai.backend.manager.services.app_config_policy.actions.update import (
    UpdateAppConfigPolicyAction,
    UpdateAppConfigPolicyActionResult,
)
from ai.backend.manager.services.app_config_policy.service import AppConfigPolicyService


class AppConfigPolicyProcessors(AbstractProcessorPackage):
    get: ActionProcessor[GetAppConfigPolicyAction, GetAppConfigPolicyActionResult]
    search: ActionProcessor[SearchAppConfigPoliciesAction, SearchAppConfigPoliciesActionResult]
    create: ActionProcessor[CreateAppConfigPolicyAction, CreateAppConfigPolicyActionResult]
    update: ActionProcessor[UpdateAppConfigPolicyAction, UpdateAppConfigPolicyActionResult]
    purge: ActionProcessor[PurgeAppConfigPolicyAction, PurgeAppConfigPolicyActionResult]

    def __init__(
        self,
        service: AppConfigPolicyService,
        action_monitors: list[ActionMonitor],
        validators: ActionValidators,
    ) -> None:
        self.get = ActionProcessor(service.get, action_monitors)
        self.search = ActionProcessor(service.search, action_monitors)
        self.create = ActionProcessor(service.create, action_monitors)
        self.update = ActionProcessor(service.update, action_monitors)
        self.purge = ActionProcessor(service.purge, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            GetAppConfigPolicyAction.spec(),
            SearchAppConfigPoliciesAction.spec(),
            CreateAppConfigPolicyAction.spec(),
            UpdateAppConfigPolicyAction.spec(),
            PurgeAppConfigPolicyAction.spec(),
        ]
