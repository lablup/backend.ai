from __future__ import annotations

from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor.bulk import BulkActionProcessor
from ai.backend.manager.actions.processor.scope import ScopeActionProcessor
from ai.backend.manager.actions.processor.single_entity import SingleEntityActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.actions.validators import ActionValidators
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
    bulk_create: BulkActionProcessor[
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
        validators: ActionValidators,
    ) -> None:
        self.create = ScopeActionProcessor(
            service.create, action_monitors, validators=[validators.rbac.scope]
        )
        self.get = SingleEntityActionProcessor(service.get, action_monitors)
        self.admin_search = ScopeActionProcessor(service.admin_search, action_monitors)
        self.scoped_search = BulkActionProcessor(
            service.scoped_search, monitors=action_monitors, validators=[validators.rbac.bulk]
        )
        self.update = SingleEntityActionProcessor(
            service.update, action_monitors, validators=[validators.rbac.single_entity]
        )
        self.purge = SingleEntityActionProcessor(
            service.purge, action_monitors, validators=[validators.rbac.single_entity]
        )
        # bulk_create writes into scopes (not existing entities), so it uses the bulk-scope
        # validator (subject = the fragment entity type) rather than the entity-target one.
        bulk_scope = validators.rbac.bulk_scope
        self.bulk_create = BulkActionProcessor(
            service.bulk_create,
            monitors=action_monitors,
            validators=[bulk_scope] if bulk_scope is not None else None,
        )
        self.bulk_update = BulkActionProcessor(
            service.bulk_update, monitors=action_monitors, validators=[validators.rbac.bulk]
        )
        self.bulk_purge = BulkActionProcessor(
            service.bulk_purge, monitors=action_monitors, validators=[validators.rbac.bulk]
        )

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
