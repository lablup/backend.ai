from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.services.app_config_policy.actions.admin_bulk_create import (
    AdminBulkCreateAppConfigPoliciesAction,
    AdminBulkCreateAppConfigPoliciesActionResult,
)
from ai.backend.manager.services.app_config_policy.actions.admin_bulk_purge import (
    AdminBulkPurgeAppConfigPoliciesAction,
    AdminBulkPurgeAppConfigPoliciesActionResult,
)
from ai.backend.manager.services.app_config_policy.actions.admin_bulk_update import (
    AdminBulkUpdateAppConfigPoliciesAction,
    AdminBulkUpdateAppConfigPoliciesActionResult,
)
from ai.backend.manager.services.app_config_policy.actions.get import (
    GetAppConfigPolicyAction,
    GetAppConfigPolicyActionResult,
)
from ai.backend.manager.services.app_config_policy.actions.search import (
    SearchAppConfigPoliciesAction,
    SearchAppConfigPoliciesActionResult,
)
from ai.backend.manager.services.app_config_policy.service import AppConfigPolicyService


class AppConfigPolicyProcessors(AbstractProcessorPackage):
    get: ActionProcessor[GetAppConfigPolicyAction, GetAppConfigPolicyActionResult]
    search: ActionProcessor[SearchAppConfigPoliciesAction, SearchAppConfigPoliciesActionResult]
    # Bulk mutations (BEP-1052 §3)
    admin_bulk_create: ActionProcessor[
        AdminBulkCreateAppConfigPoliciesAction, AdminBulkCreateAppConfigPoliciesActionResult
    ]
    admin_bulk_update: ActionProcessor[
        AdminBulkUpdateAppConfigPoliciesAction, AdminBulkUpdateAppConfigPoliciesActionResult
    ]
    admin_bulk_purge: ActionProcessor[
        AdminBulkPurgeAppConfigPoliciesAction, AdminBulkPurgeAppConfigPoliciesActionResult
    ]

    def __init__(
        self,
        service: AppConfigPolicyService,
        action_monitors: list[ActionMonitor],
        validators: ActionValidators,
    ) -> None:
        self.get = ActionProcessor(service.get, action_monitors)
        self.search = ActionProcessor(service.search, action_monitors)
        self.admin_bulk_create = ActionProcessor(service.admin_bulk_create, action_monitors)
        self.admin_bulk_update = ActionProcessor(service.admin_bulk_update, action_monitors)
        self.admin_bulk_purge = ActionProcessor(service.admin_bulk_purge, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            GetAppConfigPolicyAction.spec(),
            SearchAppConfigPoliciesAction.spec(),
            AdminBulkCreateAppConfigPoliciesAction.spec(),
            AdminBulkUpdateAppConfigPoliciesAction.spec(),
            AdminBulkPurgeAppConfigPoliciesAction.spec(),
        ]
