from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.processor.bulk import BulkActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.services.app_config_fragment.actions.admin_bulk_create import (
    AdminBulkCreateAppConfigFragmentsAction,
    AdminBulkCreateAppConfigFragmentsActionResult,
)
from ai.backend.manager.services.app_config_fragment.actions.admin_bulk_purge import (
    AdminBulkPurgeAppConfigFragmentsAction,
    AdminBulkPurgeAppConfigFragmentsActionResult,
)
from ai.backend.manager.services.app_config_fragment.actions.admin_bulk_update import (
    AdminBulkUpdateAppConfigFragmentsAction,
    AdminBulkUpdateAppConfigFragmentsActionResult,
)
from ai.backend.manager.services.app_config_fragment.actions.admin_search import (
    AdminSearchAppConfigFragmentsAction,
    AdminSearchAppConfigFragmentsActionResult,
)
from ai.backend.manager.services.app_config_fragment.admin_service import (
    AppConfigFragmentAdminService,
)


class AppConfigFragmentAdminProcessors(AbstractProcessorPackage):
    admin_search: ActionProcessor[
        AdminSearchAppConfigFragmentsAction, AdminSearchAppConfigFragmentsActionResult
    ]
    # Bulk mutations — wrapped by BulkActionProcessor so validators
    # (RBAC, etc.) can filter entity_ids per-item before the service
    # runs. No bulk validators are wired today; the processor simply
    # forwards to the service.
    admin_bulk_create: BulkActionProcessor[
        AdminBulkCreateAppConfigFragmentsAction, AdminBulkCreateAppConfigFragmentsActionResult
    ]
    admin_bulk_update: BulkActionProcessor[
        AdminBulkUpdateAppConfigFragmentsAction, AdminBulkUpdateAppConfigFragmentsActionResult
    ]
    admin_bulk_purge: BulkActionProcessor[
        AdminBulkPurgeAppConfigFragmentsAction, AdminBulkPurgeAppConfigFragmentsActionResult
    ]

    def __init__(
        self,
        service: AppConfigFragmentAdminService,
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
            AdminSearchAppConfigFragmentsAction.spec(),
            AdminBulkCreateAppConfigFragmentsAction.spec(),
            AdminBulkUpdateAppConfigFragmentsAction.spec(),
            AdminBulkPurgeAppConfigFragmentsAction.spec(),
        ]
