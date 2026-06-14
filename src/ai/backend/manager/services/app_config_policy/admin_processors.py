from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.processor.bulk import BulkActionProcessor
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
from ai.backend.manager.services.app_config_policy.actions.admin_search import (
    AdminSearchAppConfigPoliciesAction,
    AdminSearchAppConfigPoliciesActionResult,
)
from ai.backend.manager.services.app_config_policy.admin_service import (
    AppConfigPolicyAdminService,
)


class AppConfigPolicyAdminProcessors(AbstractProcessorPackage):
    admin_search: ActionProcessor[
        AdminSearchAppConfigPoliciesAction, AdminSearchAppConfigPoliciesActionResult
    ]
    admin_bulk_create: BulkActionProcessor[
        AdminBulkCreateAppConfigPoliciesAction, AdminBulkCreateAppConfigPoliciesActionResult
    ]
    admin_bulk_update: BulkActionProcessor[
        AdminBulkUpdateAppConfigPoliciesAction, AdminBulkUpdateAppConfigPoliciesActionResult
    ]
    admin_bulk_purge: BulkActionProcessor[
        AdminBulkPurgeAppConfigPoliciesAction, AdminBulkPurgeAppConfigPoliciesActionResult
    ]

    def __init__(
        self,
        service: AppConfigPolicyAdminService,
        action_monitors: list[ActionMonitor],
        validators: ActionValidators,
    ) -> None:
        self.admin_search = ActionProcessor(service.admin_search, action_monitors)
        self.admin_bulk_create = BulkActionProcessor(service.admin_bulk_create, action_monitors)
        self.admin_bulk_update = BulkActionProcessor(service.admin_bulk_update, action_monitors)
        self.admin_bulk_purge = BulkActionProcessor(service.admin_bulk_purge, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            AdminSearchAppConfigPoliciesAction.spec(),
            AdminBulkCreateAppConfigPoliciesAction.spec(),
            AdminBulkUpdateAppConfigPoliciesAction.spec(),
            AdminBulkPurgeAppConfigPoliciesAction.spec(),
        ]
