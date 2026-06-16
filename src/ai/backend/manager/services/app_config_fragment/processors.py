from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.processor.bulk import BulkActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.services.app_config_fragment.actions.get import (
    GetAppConfigFragmentAction,
    GetAppConfigFragmentActionResult,
)
from ai.backend.manager.services.app_config_fragment.actions.get_user_app_config import (
    GetUserAppConfigAction,
    GetUserAppConfigActionResult,
)
from ai.backend.manager.services.app_config_fragment.actions.my_bulk_create import (
    MyBulkCreateAppConfigFragmentsAction,
    MyBulkCreateAppConfigFragmentsActionResult,
)
from ai.backend.manager.services.app_config_fragment.actions.my_bulk_update import (
    MyBulkUpdateAppConfigFragmentsAction,
    MyBulkUpdateAppConfigFragmentsActionResult,
)
from ai.backend.manager.services.app_config_fragment.actions.scoped_search_app_configs import (
    ScopedSearchAppConfigsAction,
    ScopedSearchAppConfigsActionResult,
)
from ai.backend.manager.services.app_config_fragment.actions.search import (
    SearchAppConfigFragmentsAction,
    SearchAppConfigFragmentsActionResult,
)
from ai.backend.manager.services.app_config_fragment.service import AppConfigFragmentService


class AppConfigFragmentProcessors(AbstractProcessorPackage):
    get: ActionProcessor[GetAppConfigFragmentAction, GetAppConfigFragmentActionResult]
    search: ActionProcessor[SearchAppConfigFragmentsAction, SearchAppConfigFragmentsActionResult]
    get_user_app_config: ActionProcessor[GetUserAppConfigAction, GetUserAppConfigActionResult]
    scoped_search_app_configs: BulkActionProcessor[
        ScopedSearchAppConfigsAction, ScopedSearchAppConfigsActionResult
    ]
    # Bulk mutations — wrapped by BulkActionProcessor so validators
    # (RBAC, etc.) can filter entity_ids per-item before the service
    # runs. No bulk validators are wired today; the processor simply
    # forwards to the service.
    my_bulk_create: BulkActionProcessor[
        MyBulkCreateAppConfigFragmentsAction, MyBulkCreateAppConfigFragmentsActionResult
    ]
    my_bulk_update: BulkActionProcessor[
        MyBulkUpdateAppConfigFragmentsAction, MyBulkUpdateAppConfigFragmentsActionResult
    ]

    def __init__(
        self,
        service: AppConfigFragmentService,
        action_monitors: list[ActionMonitor],
        validators: ActionValidators,
    ) -> None:
        self.get = ActionProcessor(service.get, action_monitors)
        self.search = ActionProcessor(service.search, action_monitors)
        self.get_user_app_config = ActionProcessor(service.get_user_app_config, action_monitors)
        self.scoped_search_app_configs = BulkActionProcessor(
            service.scoped_search_app_configs, action_monitors
        )
        self.my_bulk_create = BulkActionProcessor(service.my_bulk_create, action_monitors)
        self.my_bulk_update = BulkActionProcessor(service.my_bulk_update, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            GetAppConfigFragmentAction.spec(),
            SearchAppConfigFragmentsAction.spec(),
            GetUserAppConfigAction.spec(),
            ScopedSearchAppConfigsAction.spec(),
            MyBulkCreateAppConfigFragmentsAction.spec(),
            MyBulkUpdateAppConfigFragmentsAction.spec(),
        ]
