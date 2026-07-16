from __future__ import annotations

from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor.bulk import BulkActionProcessor
from ai.backend.manager.actions.processor.scope import ScopeActionProcessor
from ai.backend.manager.actions.processor.single_entity import SingleEntityActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.services.app_config_fragment.actions.admin_search import (
    AdminSearchAppConfigFragmentAction,
    AdminSearchAppConfigFragmentActionResult,
)
from ai.backend.manager.services.app_config_fragment.actions.bulk_create import (
    BulkCreateAppConfigFragmentAction,
    BulkCreateAppConfigFragmentActionResult,
)
from ai.backend.manager.services.app_config_fragment.actions.bulk_purge import (
    BulkPurgeAppConfigFragmentAction,
    BulkPurgeAppConfigFragmentActionResult,
)
from ai.backend.manager.services.app_config_fragment.actions.bulk_update import (
    BulkUpdateAppConfigFragmentAction,
    BulkUpdateAppConfigFragmentActionResult,
)
from ai.backend.manager.services.app_config_fragment.actions.create import (
    CreateAppConfigFragmentAction,
    CreateAppConfigFragmentActionResult,
)
from ai.backend.manager.services.app_config_fragment.actions.get import (
    GetAppConfigFragmentAction,
    GetAppConfigFragmentActionResult,
)
from ai.backend.manager.services.app_config_fragment.actions.purge import (
    PurgeAppConfigFragmentAction,
    PurgeAppConfigFragmentActionResult,
)
from ai.backend.manager.services.app_config_fragment.actions.scoped_search import (
    ScopedSearchAppConfigFragmentAction,
    ScopedSearchAppConfigFragmentActionResult,
)
from ai.backend.manager.services.app_config_fragment.actions.update import (
    UpdateAppConfigFragmentAction,
    UpdateAppConfigFragmentActionResult,
)
from ai.backend.manager.services.app_config_fragment.service import (
    AppConfigFragmentService,
)


class AppConfigFragmentProcessors(AbstractProcessorPackage):
    create: ScopeActionProcessor[CreateAppConfigFragmentAction, CreateAppConfigFragmentActionResult]
    get: SingleEntityActionProcessor[GetAppConfigFragmentAction, GetAppConfigFragmentActionResult]
    admin_search: ScopeActionProcessor[
        AdminSearchAppConfigFragmentAction, AdminSearchAppConfigFragmentActionResult
    ]
    scoped_search: BulkActionProcessor[
        ScopedSearchAppConfigFragmentAction, ScopedSearchAppConfigFragmentActionResult
    ]
    update: SingleEntityActionProcessor[
        UpdateAppConfigFragmentAction, UpdateAppConfigFragmentActionResult
    ]
    purge: SingleEntityActionProcessor[
        PurgeAppConfigFragmentAction, PurgeAppConfigFragmentActionResult
    ]
    bulk_create: ScopeActionProcessor[
        BulkCreateAppConfigFragmentAction, BulkCreateAppConfigFragmentActionResult
    ]
    bulk_update: BulkActionProcessor[
        BulkUpdateAppConfigFragmentAction, BulkUpdateAppConfigFragmentActionResult
    ]
    bulk_purge: BulkActionProcessor[
        BulkPurgeAppConfigFragmentAction, BulkPurgeAppConfigFragmentActionResult
    ]

    def __init__(
        self,
        service: AppConfigFragmentService,
        action_monitors: list[ActionMonitor],
    ) -> None:
        self.create = ScopeActionProcessor(service.create, action_monitors)
        self.get = SingleEntityActionProcessor(service.get, action_monitors)
        self.admin_search = ScopeActionProcessor(service.admin_search, action_monitors)
        self.scoped_search = BulkActionProcessor(service.scoped_search, monitors=action_monitors)
        self.update = SingleEntityActionProcessor(service.update, action_monitors)
        self.purge = SingleEntityActionProcessor(service.purge, action_monitors)
        self.bulk_create = ScopeActionProcessor(service.bulk_create, action_monitors)
        self.bulk_update = BulkActionProcessor(service.bulk_update, monitors=action_monitors)
        self.bulk_purge = BulkActionProcessor(service.bulk_purge, monitors=action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            CreateAppConfigFragmentAction.spec(),
            GetAppConfigFragmentAction.spec(),
            AdminSearchAppConfigFragmentAction.spec(),
            ScopedSearchAppConfigFragmentAction.spec(),
            UpdateAppConfigFragmentAction.spec(),
            PurgeAppConfigFragmentAction.spec(),
            BulkCreateAppConfigFragmentAction.spec(),
            BulkUpdateAppConfigFragmentAction.spec(),
            BulkPurgeAppConfigFragmentAction.spec(),
        ]
